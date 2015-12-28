"""
    Fetch AWS resources and relations
"""
import garbo.config
import os
from collections import namedtuple
from functools import partial
import logging

import boto3
import yaml
from botocore.exceptions import ClientError

__author__ = 'nati'

AWS_BASE_TYPE = 'aws'
AWS_RESOURCE_DEFAULT_PROPERTIES = ['tags', ]
Resource = namedtuple('Resource', ['type', 'id', 'created', 'properties'])


def _get_collection_iterator(collection, iterator):
    if iterator == 'all':
        return collection.all
    elif iterator == 'filter_self_owned':
        filters = [{'Name': 'owner-id', 'Values': ['self']}]
        return partial(collection.filter, Filters=filters)
    else:
        raise NotImplemented('Invalid collection iterator')


def _extract_collections(session, service_name, collections):
    if collections:
        service = session.resource(service_name)
        for collection_name, collection_config in collections.iteritems():
            collection_iterator = _get_collection_iterator(getattr(service, collection_name),
                                                           collection_config.get('iterator', 'all'))
            properties = AWS_RESOURCE_DEFAULT_PROPERTIES + collection_config.get('properties', [])
            for resource in collection_iterator():
                print Resource(type='.'.join([AWS_BASE_TYPE, resource.__class__.__name__]),
                               id=getattr(resource, collection_config.get('identifier', 'id')),
                               created=getattr(resource, collection_config.get('created', 'created'), 0),
                               properties={p: getattr(resource, p) for p in properties if getattr(resource, p, '')})


def _extract_paginators(session, service_name, paginators):
    if paginators:
        client = session.client(service_name)
        for paginator_name, pagintor_config in paginators.iteritems():
            paginator = client.get_paginator(paginator_name)
            try:
                for page in paginator.paginate():
                    for resource in page.get(pagintor_config.get('resources_key')):
                        print resource
            except ClientError:
                logging.exception('Unable to use paginator %s', paginator_name)


def extract_all(regions=None):
    """
    Extract AWS Resources and Relations

    :param session: boto3
    :param aws_mapping: boto3 mapping of Service, Collections, Resources and Relations
    """
    aws_mapping = yaml.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'aws_mapping.yaml')))
    regions = regions or garbo.config.aws.regions
    for region in regions:
        session = boto3.Session(region_name=region)
        for service_name, service_config in aws_mapping.iteritems():
            _extract_collections(session, service_name, service_config.get('collections'))
            _extract_paginators(session, service_name, service_config.get('paginators'))


if __name__ == '__main__':
    extract_all()
