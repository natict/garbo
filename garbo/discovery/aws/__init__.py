"""
    Fetch AWS resources and relations
"""

from functools import partial
import logging

import boto3
from botocore.exceptions import ClientError

__author__ = 'nati'


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
        for collection, collection_config in collections.iteritems():
            collection_iterator = _get_collection_iterator(getattr(service, collection),
                                                           collection_config.get('iterator', 'all'))
            for resource in collection_iterator():
                print resource


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


def aws_resources(aws_mapping, session=None):
    """
    Collect AWS Resources from boto3 Collections and Paginators

    :param session: boto3
    :param aws_mapping: boto3 mapping of Service, Collections, Resources and Relations
    """
    session = session or boto3
    for service_name, service_config in aws_mapping.iteritems():
        _extract_collections(session, service_name, service_config.get('collections'))
        _extract_paginators(session, service_name, service_config.get('paginators'))
