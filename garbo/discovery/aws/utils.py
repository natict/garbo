__author__ = 'nati'

import logging

import boto.ec2

from garbo import config

_resource_collectors = set()


def aws_collector(conn_obj=None):
    """
    Collect AWS collectors to a global module set

    :param conn_obj: AWS connection function (default: EC2 connection)
    """

    def wrap(f):
        def wrapped_f(conn):
            if conn_obj:
                # convert the EC2 connection to conn_obj
                conn = conn_obj(conn.region.name,
                                aws_access_key_id=conn.provider.access_key,
                                aws_secret_access_key=conn.provider.secret_key)
            logging.info('calling %s', f.__name__)
            # wrapping the generator
            for r in f(conn):
                yield r

        _resource_collectors.add(wrapped_f)
        return wrapped_f

    return wrap


def collect_all(aws_access_key=None, aws_secret_key=None):
    """
    Yield all EC2 resources and relations associated with an AWS account

    :param aws_access_key:
    :param aws_secret_key:
    """
    aws_access_key = aws_access_key or config.aws.access_key
    aws_secret_key = aws_secret_key or config.aws.secret_access_key

    regions = config.aws.regions or (r.name for r in boto.ec2.regions())
    for region in regions:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=aws_access_key,
                                          aws_secret_access_key=aws_secret_key)
        logging.info('running AWS collectors on %s', region)

        for collector in _resource_collectors:
            try:
                for item in collector(conn):
                    yield item
            except boto.exception.BotoServerError as e:
                logging.warn('unable to run collector %s for region %s: %s',
                             collector.__name__, region, e.message)
