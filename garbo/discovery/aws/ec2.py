"""
    This a garbo discovery service for AWS EC2 resources
"""
import logging

import dateutil.parser
import boto.ec2
import boto.exception

from garbo import config
from garbo.model.aws.ebs_snapshot import EBSSnapshot
from garbo.model.aws.ebs_volume import EBSVolume
from garbo.model.aws.image import Image
from garbo.model.aws.instance import Instance
from garbo.model.relation import Relation

__author__ = 'nati'

_resource_collectors = set()


def aws_collector(f):
    _resource_collectors.add(f)


@aws_collector
def snapshots(conn):
    # only iterate snapshots created by this account
    for snapshot in conn.get_all_snapshots(owner='self'):
        yield EBSSnapshot(region=conn.region.name, snapshot_id=snapshot.id,
                          created=dateutil.parser.parse(snapshot.start_time))


@aws_collector
def images(conn):
    # only iterate images created by this account
    for image in conn.get_all_images(owners='self'):
        image_resource = Image(region=conn.region.name, image_id=image.id,
                               created=dateutil.parser.parse(image.creationDate))
        yield image_resource
        # Images can have mapping to an EBS snapshot (stored in S3)
        for snapshot_id in set([v.snapshot_id for v in image.block_device_mapping.itervalues() if v.snapshot_id]):
            # only yield relations to snapshots within the same account
            if conn.get_all_snapshots(snapshot_ids=[snapshot_id], owner='self'):
                yield Relation(image_resource,
                               EBSSnapshot(region=conn.region.name, snapshot_id=snapshot_id))


@aws_collector
def instances(conn):
    for instance in conn.get_only_instances():
        instance_resource = Instance(region=conn.region.name, instance_id=instance.id,
                                     created=dateutil.parser.parse(instance.launch_time),
                                     used=Instance.is_used(instance))
        yield instance_resource
        # only yield relations for self-owned images
        if conn.get_all_images(image_ids=[instance.image_id], owners='self'):
            yield Relation(instance_resource.urid(),
                           Image(region=conn.region.name, image_id=instance.image_id))


@aws_collector
def ebs_volumes(conn):
    for volume in conn.get_all_volumes():
        ebs_volume_resource = EBSVolume(region=conn.region.name, volume_id=volume.id,
                                        created=dateutil.parser.parse(volume.create_time))
        yield ebs_volume_resource
        # If volume is attached, yield a relation to the instance
        if volume.attach_data.status in ('attaching', 'attached'):
            yield Relation(Instance(region=conn.region.name,
                                    instance_id=volume.attach_data.instance_id),
                           ebs_volume_resource)


def collect_all(aws_access_key=None, aws_secret_key=None):
    """
    Yield all EC2 resources and relations associated with an AWS account

    :param aws_access_key:
    :param aws_secret_key:
    """
    aws_access_key = aws_access_key or config.aws.access_key
    aws_secret_key = aws_secret_key or config.aws.secret_access_key

    regions = ('us-east-1',) if config.aws.debug else (r.name for r in boto.ec2.regions())
    for region in regions:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=aws_access_key,
                                          aws_secret_access_key=aws_secret_key)
        for collector in _resource_collectors:
            try:
                for item in collector(conn):
                    yield item
            except boto.exception.BotoServerError, e:
                logging.warn('unable to run collector %s for region %s: %s',
                             collector.__name__, region.name, e.message)
