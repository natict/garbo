"""
    This a garbo discovery service for AWS EC2 resources
"""
import logging
from samba.netcmd.dns import dns_name_equal

import dateutil.parser
import boto.ec2
import boto.ec2.elb
import boto.exception

from garbo import config
from garbo.model.aws.ebs_snapshot import EBSSnapshot
from garbo.model.aws.ebs_volume import EBSVolume
from garbo.model.aws.image import Image
from garbo.model.aws.instance import Instance
from garbo.model.aws.load_balancer import LoadBalancer
from garbo.model.aws.security_group import SecurityGroup
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
def load_balancers(conn):
    # Convert EC2 connection to ELB connection
    conn = boto.ec2.elb.connect_to_region(conn.region.name,
                                          aws_access_key_id=conn.provider.access_key,
                                          aws_secret_access_key=conn.provider.secret_key)
    for elb in conn.get_all_load_balancers():
        lb_resource = LoadBalancer(region=conn.region.name, dns_name=elb.dns_name,
                                   created=dateutil.parser.parse(elb.created_time))
        yield lb_resource
        # security groups relations
        for group_id in elb.security_groups:
            yield Relation(lb_resource,
                           SecurityGroup(region=conn.region.name, group_id=group_id))
        # instances relations
        for instance_id in {i.id for i in elb.instances}:
            yield Relation(lb_resource,
                           Instance(region=conn.region.name, instance_id=instance_id))


@aws_collector
def security_groups(conn):
    for group in conn.get_all_security_groups():
        # Fun fact: there is no creation/modification date associated with AWS security groups
        yield SecurityGroup(region=conn.region.name, group_id=group.id)


@aws_collector
def images(conn):
    # only iterate images created by this account
    for image in conn.get_all_images(owners='self'):
        image_resource = Image(region=conn.region.name, image_id=image.id,
                               created=dateutil.parser.parse(image.creationDate))
        yield image_resource
        # Images can have mapping to an EBS snapshot (stored in S3)
        for snapshot_id in {v.snapshot_id for v in image.block_device_mapping.itervalues() if v.snapshot_id}:
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
            yield Relation(instance_resource,
                           Image(region=conn.region.name, image_id=instance.image_id))
        # security groups relations
        for group_id in {sg.id for sg in instance.groups}:
            yield Relation(instance_resource,
                           SecurityGroup(region=conn.region.name, group_id=group_id))


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

    regions = config.aws.regions or (r.name for r in boto.ec2.regions())
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
                             collector.__name__, region, e.message)
