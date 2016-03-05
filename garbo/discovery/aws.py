"""
    Fetch AWS resources and relations
"""

import logging
import os
from types import NoneType

import boto3
import yaml
from boto3.resources.collection import CollectionManager
from botocore.exceptions import ClientError
from botocore.utils import parse_to_aware_datetime

import garbo.config
from garbo.model import Resource, Relation
from garbo.utils import rgetattr, rget, squash_list

__author__ = 'nati'


class AWSResource(Resource):
    AWS_TYPE_BASE = 'aws'
    AWS_TYPE_SEP = '.'

    def __init__(self, service, resource_type, identifier, created=None, properties=None):
        aws_type = AWSResource.generate_aws_type(service, resource_type)
        created = parse_to_aware_datetime(created) if created else None  # normalize creation date
        properties = {k: v for k, v in (properties or {}).iteritems() if v}  # filter empty properties
        super(AWSResource, self).__init__(aws_type, identifier, created, properties)

    @staticmethod
    def generate_aws_type(service, resource_type):
        return AWSResource.AWS_TYPE_SEP.join([AWSResource.AWS_TYPE_BASE, resource_type]
                                             if AWSResource.AWS_TYPE_SEP in resource_type else [service, resource_type])


class AWSRelation(Relation):
    pass


def _resources_from_collection(collection, iterator_config=None):
    iterator_config = iterator_config or {'all': {}}
    if not isinstance(iterator_config, dict):
        raise NotImplemented('iterator must be dict of a function name and kwargs (iterator=%s)' % str(iterator_config))
    for iterator_fn, iterator_kwargs in iterator_config.iteritems():
        iterator_kwargs = iterator_kwargs or {}
        for resource in getattr(collection, iterator_fn)(**iterator_kwargs):
            yield resource


def _referenced_resources(references_map, src_resource, service_name):
    references_map = references_map or {}
    for reference_name, reference_config in references_map.iteritems():
        resources = (rget(src_resource, reference_name) if isinstance(src_resource, dict) else
                     rgetattr(src_resource, reference_name, '')) or []
        if 'reference_path' in reference_config:
            # Support references of type [{'reference_path': [{'ref_id_key':'ref_id'}, {}]}, {}, ...]
            resources = [rget(r, reference_config['reference_path']) for r in
                         resources if r]
        elif isinstance(resources, CollectionManager):
            resources = resources.all()
        elif not isinstance(resources, list):
            resources = [resources]
        resource_type = reference_config.get('type')
        id_attribute = reference_config.get('identifier', 'id')
        for resource in squash_list(resources):
            resource_id = resource if isinstance(resource, basestring) else \
                rget(resource, id_attribute) if isinstance(resource, dict) else rgetattr(resource, id_attribute)
            if all((resource_type, resource_id)):
                yield AWSResource(service=service_name,
                                  resource_type=resource_type,
                                  identifier=resource_id)
            elif not reference_config.get('ignore_missing', False):
                logging.warn('Referenced resource type or identifier is missing '
                             '(type=%s, id=%s, resource=%s)',
                             resource_type, resource_id, resource)


def _extract_collections(session, service_name, collections):
    builtin_types = (str, unicode, int, long, float, bool, NoneType, list, tuple, dict)
    if collections:
        service = session.resource(service_name)
        for collection_name, collection_config in collections.iteritems():
            collection = getattr(service, collection_name)
            resource_type = collection_config.get('type')
            resource_created_attr = collection_config.get('created', 'create_date')
            for resource in _resources_from_collection(collection, collection_config.get('iterator')):
                resource_id = getattr(resource, collection_config.get('identifier', 'id'))
                if not all((resource_type, resource_id)):
                    logging.warn('Resource type or identifier is missing (type=%s, id=%s, resource=%s)',
                                 resource_type, resource_id, resource)
                    continue
                aws_resource = AWSResource(service=service_name,
                                           resource_type=resource_type,
                                           identifier=resource_id,
                                           created=getattr(resource, resource_created_attr, ''),
                                           properties={p: repr(getattr(resource, p, '')) for p in dir(resource)
                                                       if not p.startswith('_') and isinstance(getattr(resource, p),
                                                                                               builtin_types)})
                yield aws_resource
                for referenced_resource in _referenced_resources(collection_config.get('references'),
                                                                 resource, service_name):
                    yield AWSRelation(src_resource=aws_resource, dst_resource=referenced_resource)


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
            for resource in _resources_from_paginator(paginator, pagintor_config.get('resources_key')):
                resource_id = resource.get(pagintor_config.get('identifier', 'id'))
                if not all((resource_type, resource_id)):
                    logging.warn('Resource type or identifier is missing (type=%s, id=%s, resource=%s)',
                                 resource_type, resource_id, resource)
                    continue
                aws_resource = AWSResource(service=service_name,
                                           resource_type=resource_type,
                                           identifier=resource_id,
                                           created=resource.get(pagintor_config.get('created', 'CreatedTime'), 0),
                                           properties=resource)
                yield aws_resource
                for referenced_resource in _referenced_resources(pagintor_config.get('references'),
                                                                 resource, service_name):
                    yield AWSRelation(src_resource=aws_resource, dst_resource=referenced_resource)


def print_mapping_stats(aws_mapping, verbose=False):
    resources, relations = set(), set()
    for service_name, service_config in aws_mapping.iteritems():
        for service_iterator, service_iterator_config in service_config.iteritems():
            if isinstance(service_iterator_config, dict):
                for resource_name, resource_config in service_iterator_config.iteritems():
                    resource_type = AWSResource.generate_aws_type(service_name, resource_config.get('type'))
                    resources.add(resource_type)
                    for reference_name, reference_config in resource_config.get('references', {}).iteritems():
                        reference_type = AWSResource.generate_aws_type(service_name, reference_config.get('type'))
                        relations.add((resource_type, reference_type))
    print 'AWS Discovery loaded {} resource types and {} relation types'.format(len(resources), len(relations))
    if verbose:
        print 'Resources: ', resources
        print 'Relation: ', relations


def discover_all(regions=None):
    """
    Extract AWS Resources and Relations (in no particular order)
    :type regions: list
    :param regions: list of region names to extract from
    """
    aws_mapping = yaml.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'aws_mapping.yaml')))
    print_mapping_stats(aws_mapping)
    regions = regions or garbo.config.aws.regions

    for service_name, service_config in aws_mapping.iteritems():
        for region in (regions if service_config.get('regional', True) else regions[:1]):
            session = boto3.Session(region_name=region)
            for e in _extract_collections(session, service_name, service_config.get('collections')):
                yield e
            for e in _extract_paginators(session, service_name, service_config.get('paginators')):
                yield e
