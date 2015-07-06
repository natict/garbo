"""
    TODO
"""
from datetime import datetime

import boto.elasticache
import boto.utils

from garbo.discovery.aws.utils import aws_collector
from garbo.model import Relation
from garbo.model.aws import CacheCluster, SecurityGroup

__author__ = 'nati'


@aws_collector(boto.elasticache.connect_to_region)
def cache_clusters(conn):
    """
    Collect AWS Elastic Cache clusters

    :param conn: boto EC2 connection
    """
    # TODO: add paging (currently supporting only the first 100)
    all_cache_clusters = conn.describe_cache_clusters() \
        .get('DescribeCacheClustersResponse', {}) \
        .get('DescribeCacheClustersResult', {}) \
        .get('CacheClusters', [])
    for cache_cluster in all_cache_clusters:
        cc_resource = CacheCluster(region=conn.region.name, resource_id=cache_cluster.get('CacheClusterId'),
                                   created=datetime.utcfromtimestamp(cache_cluster.get('CacheClusterCreateTime')))
        yield cc_resource
        # security groups relations
        for sg in cache_cluster.get('SecurityGroups', []):
            if sg.get('Status') == 'active':
                yield Relation(cc_resource,
                               SecurityGroup(region=conn.region.name,
                                             resource_id=sg.get('SecurityGroupId')),
                               dependency=True)
                # TODO: CacheParameterGroup relations
