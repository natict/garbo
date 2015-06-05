"""
    This a garbo discovery service for AWS EC2 resources
"""
import logging

import dateutil.parser
import boto.ec2
import boto.ec2.elb
import boto.exception

from garbo import config
from garbo.model.aws.ec2 import EBSSnapshot, EBSVolume, Image, Instance, LoadBalancer, SecurityGroup
from garbo.model import Relation

__author__ = 'nati'

_resource_collectors = set()


def aws_collector(f):
    """
    Collect AWS collectors to a global module set

    :param f:  AWS collector function, getting boto EC2 connection and yielding resources and/or relations
    """
    _resource_collectors.add(f)
    return f


@aws_collector
def snapshots(conn):
    """
    Collect EC2 EBS Snapshots created by this account

    :param conn: boto EC2 connection
    """
    volume_ids = [v.id for v in conn.get_all_volumes()]
    for snapshot in conn.get_all_snapshots(owner='self'):
        snapshot_resource = EBSSnapshot(region=conn.region.name, resource_id=snapshot.id,
                                        created=dateutil.parser.parse(snapshot.start_time))
        yield snapshot_resource
        if snapshot.volume_id in volume_ids:
            yield Relation(snapshot_resource,
                           EBSVolume(region=conn.region.name, resource_id=snapshot.volume_id))


@aws_collector
def load_balancers(conn):
    """
    Collect EC2 Elastic Load Balances (ELBs)

    :param conn: boto EC2 connection
    """
    # Convert EC2 connection to ELB connection
    conn = boto.ec2.elb.connect_to_region(conn.region.name,
                                          aws_access_key_id=conn.provider.access_key,
                                          aws_secret_access_key=conn.provider.secret_key)
    for elb in conn.get_all_load_balancers():
        lb_resource = LoadBalancer(region=conn.region.name, resource_id=elb.dns_name,
                                   created=dateutil.parser.parse(elb.created_time))
        yield lb_resource
        # security groups relations
        for group_id in elb.security_groups:
            yield Relation(lb_resource,
                           SecurityGroup(region=conn.region.name, resource_id=group_id),
                           dependency=True)
        # instances relations
        for instance_id in {i.id for i in elb.instances}:
            yield Relation(lb_resource,
                           Instance(region=conn.region.name, resource_id=instance_id),
                           dependency=True)


@aws_collector
def security_groups(conn):
    """
    Collect EC2 Security Groups

    :param conn: boto EC2 connection
    """
    for group in conn.get_all_security_groups():
        # Fun fact: there is no creation/modification date associated with AWS security groups
        yield SecurityGroup(region=conn.region.name, resource_id=group.id)
        # TODO: add cross-group dependency


@aws_collector
def images(conn):
    """
    Collect EC2 Amazon Machine Images (AMIs) created by this account

    :param conn: boto EC2 connection
    """
    snapshot_ids = [s.id for s in conn.get_all_snapshots(owner='self')]
    for image in conn.get_all_images(owners='self'):
        image_resource = Image(region=conn.region.name, resource_id=image.id,
                               created=dateutil.parser.parse(image.creationDate))
        yield image_resource
        # Images can have mapping to an EBS snapshot (stored in S3)
        for snapshot_id in {v.snapshot_id for v in image.block_device_mapping.values()
                            if v.snapshot_id in snapshot_ids}:
            yield Relation(image_resource,
                           EBSSnapshot(region=conn.region.name, resource_id=snapshot_id),
                           dependency=True)


@aws_collector
def instances(conn):
    """
    Collect EC2 Instances

    :param conn: boto EC2 connection
    """
    image_ids = [i.id for i in conn.get_all_images(owners='self')]
    for instance in conn.get_only_instances():
        instance_resource = Instance(region=conn.region.name, resource_id=instance.id,
                                     created=dateutil.parser.parse(instance.launch_time),
                                     used=Instance.is_used(instance))
        yield instance_resource
        # only yield relations for self-owned images
        if instance.image_id in image_ids:
            yield Relation(instance_resource,
                           Image(region=conn.region.name, resource_id=instance.image_id))
        # security groups relations
        for group_id in {sg.id for sg in instance.groups}:
            yield Relation(instance_resource,
                           SecurityGroup(region=conn.region.name, resource_id=group_id),
                           dependency=True)


@aws_collector
def ebs_volumes(conn):
    """
    Collect EC2 EBS Volumes

    :param conn: boto EC2 connection
    """
    snapshot_ids = [s.id for s in conn.get_all_snapshots(owner='self')]
    for volume in conn.get_all_volumes():
        ebs_volume_resource = EBSVolume(region=conn.region.name, resource_id=volume.id,
                                        created=dateutil.parser.parse(volume.create_time))
        yield ebs_volume_resource
        # If volume is attached, yield a relation to the instance
        if volume.attach_data.status in ('attaching', 'attached'):
            yield Relation(Instance(region=conn.region.name,
                                    resource_id=volume.attach_data.instance_id),
                           ebs_volume_resource,
                           dependency=True)
        # Which snapshot was this volume created from
        if volume.snapshot_id in snapshot_ids:
            yield Relation(ebs_volume_resource,
                           EBSSnapshot(region=conn.region.name, resource_id=volume.snapshot_id))


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
            except boto.exception.BotoServerError as e:
                logging.warn('unable to run collector %s for region %s: %s',
                             collector.__name__, region, e.message)
