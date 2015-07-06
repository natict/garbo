"""
    This a garbo discovery service for AWS EC2 resources
"""

import boto.utils
import boto.ec2
import boto.ec2.autoscale
import boto.ec2.elb
import boto.exception

from garbo.discovery.aws.utils import aws_collector
from garbo.model.aws import EBSSnapshot, EBSVolume, Image, Instance, LoadBalancer, SecurityGroup, ElasticIP, \
    KeyPair, AutoScalingGroup, LaunchConfiguration
from garbo.model import Relation

__author__ = 'nati'


@aws_collector()
def snapshots(conn):
    """
    Collect EC2 EBS Snapshots created by this account

    :param conn: boto EC2 connection
    """
    volume_ids = [v.id for v in conn.get_all_volumes()]
    for snapshot in conn.get_all_snapshots(owner='self'):
        snapshot_resource = EBSSnapshot(region=conn.region.name, resource_id=snapshot.id,
                                        created=boto.utils.parse_ts(snapshot.start_time))
        yield snapshot_resource
        if snapshot.volume_id in volume_ids:
            yield Relation(snapshot_resource,
                           EBSVolume(region=conn.region.name, resource_id=snapshot.volume_id))


@aws_collector(conn_obj=boto.ec2.elb.connect_to_region)
def load_balancers(conn):
    """
    Collect EC2 Elastic Load Balances (ELBs)

    :param conn: boto EC2 connection
    """
    for elb in conn.get_all_load_balancers():
        lb_resource = LoadBalancer(region=conn.region.name, resource_id=elb.name,
                                   created=boto.utils.parse_ts(elb.created_time))
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


@aws_collector()
def security_groups(conn):
    """
    Collect EC2 Security Groups

    :param conn: boto EC2 connection
    """
    for group in conn.get_all_security_groups():
        # Fun fact: there is no creation/modification date associated with AWS security groups
        sg_resource = SecurityGroup(region=conn.region.name, resource_id=group.id)
        yield sg_resource
        # add cross-group dependency
        for group_id in {g.group_id for r in group.rules + group.rules_egress for g in r.grants
                         if g.group_id and g.owner_id == group.owner_id}:
            yield Relation(sg_resource,
                           SecurityGroup(region=conn.region.name, resource_id=group_id),
                           dependency=True)


@aws_collector()
def key_pairs(conn):
    """
    Collect EC2 Key Pairs

    :param conn: boto EC2 connection
    """
    for key_pair in conn.get_all_key_pairs():
        yield KeyPair(region=conn.region.name, resource_id=key_pair.name)


@aws_collector()
def launch_configurations(conn):
    """
    Collect EC2 Elastic IPs

    :param conn: boto EC2 connection
    """
    # using EC2 connection to fetch self owned image ids
    image_ids = [i.id for i in conn.get_all_images(owners='self')]
    # switching to autoscale connection to fetch Launch Configurations
    conn = boto.ec2.autoscale.connect_to_region(conn.region.name,
                                                aws_access_key_id=conn.provider.access_key,
                                                aws_secret_access_key=conn.provider.secret_key)
    for lc in conn.get_all_launch_configurations():
        # Fun Fact: LaunchConfiguration created_time is not an ISO 8601, but a parsed datetime
        lc_resource = LaunchConfiguration(region=conn.region.name, resource_id=lc.name,
                                          created=lc.created_time)
        yield lc_resource
        # key pair relation
        if lc.key_name:
            yield Relation(lc_resource,
                           KeyPair(region=conn.region.name, resource_id=lc.key_name),
                           dependency=True)
        # self owned image relation
        if lc.image_id in image_ids:
            yield Relation(lc_resource,
                           Image(region=conn.region.name, resource_id=lc.image_id),
                           dependency=True)
        # security groups relations
        for group_id in set(lc.security_groups):
            yield Relation(lc_resource,
                           SecurityGroup(region=conn.region.name, resource_id=group_id),
                           dependency=True)


@aws_collector(conn_obj=boto.ec2.autoscale.connect_to_region)
def auto_scaling_groups(conn):
    """
    Collect EC2 Elastic IPs

    :param conn: boto EC2 connection
    """
    for asg in conn.get_all_groups():
        asg_resource = AutoScalingGroup(region=conn.region.name, resource_id=asg.name,
                                        created=boto.utils.parse_ts(asg.created_time))
        yield asg_resource
        # Auto Scaling Group is associated with multiple instances
        for instance_id in {i.instance_id for i in asg.instances}:
            yield Relation(asg_resource,
                           Instance(region=conn.region.name, resource_id=instance_id),
                           dependency=True)
        # Launch Configuration
        if asg.launch_config_name:
            yield Relation(asg_resource,
                           LaunchConfiguration(region=conn.region.name, resource_id=asg.launch_config_name),
                           dependency=True)
        # Associated Load Balancers
        for lb_name in asg.load_balancers:
            yield Relation(LoadBalancer(region=conn.region.name, resource_id=lb_name),
                           asg_resource,
                           dependency=True)


@aws_collector()
def elastic_ips(conn):
    """
    Collect EC2 Elastic IPs

    :param conn: boto EC2 connection
    """
    for address in conn.get_all_addresses():
        address_resource = ElasticIP(region=conn.region.name, resource_id=address.public_ip)
        yield address_resource
        # an address is usually associated with an instance
        if address.instance_id:
            yield Relation(Instance(region=conn.region.name, resource_id=address.instance_id),
                           address_resource,
                           dependency=True)


@aws_collector()
def images(conn):
    """
    Collect EC2 Amazon Machine Images (AMIs) created by this account

    :param conn: boto EC2 connection
    """
    snapshot_ids = [s.id for s in conn.get_all_snapshots(owner='self')]
    for image in conn.get_all_images(owners='self'):
        image_resource = Image(region=conn.region.name, resource_id=image.id,
                               created=boto.utils.parse_ts(image.creationDate))
        yield image_resource
        # Images can have mapping to an EBS snapshot (stored in S3)
        for snapshot_id in {v.snapshot_id for v in image.block_device_mapping.values()
                            if v.snapshot_id in snapshot_ids}:
            yield Relation(image_resource,
                           EBSSnapshot(region=conn.region.name, resource_id=snapshot_id),
                           dependency=True)


@aws_collector()
def instances(conn):
    """
    Collect EC2 Instances

    :param conn: boto EC2 connection
    """
    image_ids = [i.id for i in conn.get_all_images(owners='self')]
    for instance in conn.get_only_instances():
        instance_resource = Instance(region=conn.region.name, resource_id=instance.id,
                                     created=boto.utils.parse_ts(instance.launch_time),
                                     used=Instance.is_running(instance),
                                     cleanup_candidate=Instance.is_cleanup_candidate(instance))
        yield instance_resource
        if instance.key_name:
            yield Relation(instance_resource,
                           KeyPair(region=conn.region.name, resource_id=instance.key_name),
                           dependency=True)
        # only yield relations for self-owned images
        if instance.image_id in image_ids:
            yield Relation(instance_resource,
                           Image(region=conn.region.name, resource_id=instance.image_id))
        # security groups relations
        for group_id in {sg.id for sg in instance.groups}:
            yield Relation(instance_resource,
                           SecurityGroup(region=conn.region.name, resource_id=group_id),
                           dependency=True)


@aws_collector()
def ebs_volumes(conn):
    """
    Collect EC2 EBS Volumes

    :param conn: boto EC2 connection
    """
    snapshot_ids = [s.id for s in conn.get_all_snapshots(owner='self')]
    for volume in conn.get_all_volumes():
        ebs_volume_resource = EBSVolume(region=conn.region.name, resource_id=volume.id,
                                        created=boto.utils.parse_ts(volume.create_time))
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
