"""
    This a garbo discovery service for AWS EC2 resources
"""
import logging

import boto.ec2
import boto.exception

from garbo import config
from garbo.model.aws.instance import Instance

__author__ = 'nati'

_resource_collectors = set()


def resource_collector(f):
    _resource_collectors.add(f)


@resource_collector
def instance_collector(conn):
    for instance in conn.get_only_instances():
        yield Instance(region=conn.region.name, instance_id=instance.id)


def collect_all(aws_access_key=None, aws_secret_key=None):
    """
    Yield all EC2 resources and relations associated with an AWS account

    :param aws_access_key:
    :param aws_secret_key:
    """
    aws_access_key = aws_access_key or config.aws.access_key
    aws_secret_key = aws_secret_key or config.aws.secret_access_key

    for region in boto.ec2.regions():
        conn = boto.ec2.connect_to_region(region.name,
                                          aws_access_key_id=aws_access_key,
                                          aws_secret_access_key=aws_secret_key)
        for collector in _resource_collectors:
            try:
                for resource in collector(conn):
                    yield resource
            except boto.exception.BotoServerError, e:
                logging.warn('unable to run collector %s for region %s: %s',
                             collector.__name__, region.name, e.message)
