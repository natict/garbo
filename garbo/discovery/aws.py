"""
    Fetch AWS resources and relations
"""

import garbo.config
import os
from collections import namedtuple
from functools import partial
import logging

import boto3
from boto3.resources.collection import CollectionManager
from funcy import first
import yaml
from botocore.exceptions import ClientError

__author__ = 'nati'

AWS_BASE_TYPE = 'aws'
AWS_RESOURCE_DEFAULT_PROPERTIES = ['tags', 'state']
Resource = namedtuple('Resource', ['type', 'id', 'created', 'properties'])
Relation = namedtuple('Relation', ['src_type', 'src_id', 'dst_type', 'dst_id'])


def _get_collection_iterator(collection, iterator):
    if iterator == 'all':
        return collection.all
    elif isinstance(iterator, dict):
        iterator_fn = first(iterator)
        iterator_kwargs = iterator[iterator_fn] or {}
        return partial(getattr(collection, iterator_fn), **iterator_kwargs)
    else:
        raise NotImplemented('iterator must be "all" or dict of a function and kwargs (iterator=%s)' % str(iterator))


def rgetattr(obj, name, default=None):
    """
    recursive getattr() implementation
    """
    assert isinstance(name, basestring)
    lname, _, rname = name.partition('.')
    try:
        if rname:
            return rgetattr(getattr(obj, lname), rname, default)
        else:
            return getattr(obj, lname, default)
    except AttributeError as e:
        if default is None:
            raise e
        else:
            return default


def rget(d, key, default=None):
    """
    recursive dict.get() implementation
    """
    assert isinstance(key, basestring)
    lkey, _, rkey = key.partition('.')
    if isinstance(d, dict):
        if rkey:
            return rget(d.get(lkey), rkey, default)
        else:
            return d.get(lkey, default)
    else:
        return default


def squash_list(l):
    ret = []
    for e in l:
        ret.extend(squash_list(e) if isinstance(e, list) else [e])
    return ret


def _extract_collections(session, service_name, collections):
    if collections:
        service = session.resource(service_name)
        for collection_name, collection_config in collections.iteritems():
            collection_iterator = _get_collection_iterator(getattr(service, collection_name),
                                                           collection_config.get('iterator', 'all'))
            properties = AWS_RESOURCE_DEFAULT_PROPERTIES + collection_config.get('properties', [])
            resource_type = collection_config.get('type')
            for resource in collection_iterator():
                # TODO: replace the namedtuple with a AWSResource class, apply AWS specific logic there (type prefix, date convertion etc.)
                resource_id = getattr(resource, collection_config.get('identifier', 'id'))
                if resource_type and resource_id:
                    print Resource(type=resource_type,
                                   id=resource_id,
                                   created=getattr(resource, collection_config.get('created', 'create_date'), 0),
                                   properties={p: getattr(resource, p) for p in properties if getattr(resource, p, '')})
                    for reference_name, reference_config in collection_config.get('references', {}).iteritems():
                        reference_resources = getattr(resource, reference_name, None) or []
                        if 'reference_path' in reference_config:
                            reference_resources = [rget(r, reference_config['reference_path']) for r in
                                                   reference_resources if r]
                        elif isinstance(reference_resources, CollectionManager):
                            reference_resources = reference_resources.all()
                        elif not isinstance(reference_resources, list):
                            reference_resources = [reference_resources]
                        for other_resource in squash_list(reference_resources):
                            other_resource_type = reference_config.get('type')
                            id_attribute = reference_config.get('identifier', 'id')
                            other_resource_id = other_resource if isinstance(other_resource, basestring) else \
                                rget(other_resource, id_attribute) if isinstance(other_resource, dict) else \
                                    rgetattr(other_resource, id_attribute)
                            if other_resource_type and other_resource_id:
                                print Relation(src_type=resource_type,
                                               src_id=resource_id,
                                               dst_type=other_resource_type,
                                               dst_id=other_resource_id)
                            elif not reference_config.get('ignore_missing', False):
                                logging.warn('Referenced resource type or identifier is missing '
                                             '(type=%s, id=%s, resource=%s)',
                                             other_resource_type, other_resource_id, other_resource)
                else:
                    logging.warn('Resource type or identifier is missing (type=%s, id=%s, resource=%s)',
                                 resource_type, resource_id, resource)


def _resources_from_paginator(paginator, resources_key):
    try:
        for page in paginator.paginate():
            for resource in page.get(resources_key):
                yield resource
    except ClientError:
        logging.exception('Unable to use paginator %s', paginator)


def _extract_paginators(session, service_name, paginators):
    if paginators:
        client = session.client(service_name)
        for paginator_name, pagintor_config in paginators.iteritems():
            paginator = client.get_paginator(paginator_name)
            resource_type = pagintor_config.get('type')
            resource_properties = pagintor_config.get('properties', [])  # TODO
            for resource in _resources_from_paginator(paginator, pagintor_config.get('resources_key')):
                resource_id = resource.get(pagintor_config.get('identifier', 'id'))
                print Resource(type=resource_type,
                               id=resource_id,
                               created=resource.get(pagintor_config.get('created', 'create_date'), 0),
                               properties={p: rget(resource, p) for p in resource_properties if rget(resource, p)})
                for reference_name, reference_config in pagintor_config.get('references', {}).iteritems():
                    reference_resources = rget(resource, reference_name) or []
                    if not isinstance(reference_resources, list):
                        reference_resources = [reference_resources]
                    for other_resource in squash_list(reference_resources):
                        other_resource_type = reference_config.get('type')
                        id_attribute = reference_config.get('identifier', 'id')
                        other_resource_id = other_resource if isinstance(other_resource, basestring) else \
                            rget(other_resource, id_attribute)
                        if other_resource_type and other_resource_id:
                            print Relation(src_type=resource_type,
                                           src_id=resource_id,
                                           dst_type=other_resource_type,
                                           dst_id=other_resource_id)
                        elif not reference_config.get('ignore_missing', False):
                            logging.warn('Referenced resource type or identifier is missing '
                                         '(type=%s, id=%s, resource=%s)',
                                         other_resource_type, other_resource_id, other_resource)


def extract_all(regions=None):
    """
    Extract AWS Resources and Relations
    """
    aws_mapping = yaml.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'aws_mapping.yaml')))
    regions = regions or garbo.config.aws.regions

    for service_name, service_config in aws_mapping.iteritems():
        for region in (regions if service_config.get('regional', True) else regions[:1]):
            session = boto3.Session(region_name=region)
            _extract_collections(session, service_name, service_config.get('collections'))
            _extract_paginators(session, service_name, service_config.get('paginators'))


if __name__ == '__main__':
    extract_all()
