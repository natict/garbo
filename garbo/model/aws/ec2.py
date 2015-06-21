"""
    garbo EC2 resources
"""

from garbo.model import AbstractResource

__author__ = 'nati'


class EC2BaseResource(AbstractResource):
    def __init__(self, region, resource_id, created=None, used=False):
        rid = '/'.join((region, resource_id))
        super(EC2BaseResource, self).__init__(provider='AWS',
                                              rtype=self.__class__.__name__,
                                              rid=rid,
                                              created=created,
                                              used=used)

    def cleanup(self):
        # TODO: implement generic EC2 cleanup method
        super(EC2BaseResource, self).cleanup()


class EBSSnapshot(EC2BaseResource):
    pass


class EBSVolume(EC2BaseResource):
    pass


class Image(EC2BaseResource):
    pass


class LoadBalancer(EC2BaseResource):
    pass


class SecurityGroup(EC2BaseResource):
    pass


class Instance(EC2BaseResource):
    # Instance state codes considered as used,
    #   see: http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    __USED_STATE_CODES = (0, 16)

    @classmethod
    def is_used(cls, instance):
        """
        static function to decide if an instance is running
        :param instance: boto.ec2.instance.Instance object
        :return: True if instance is running (or pending running), False otherwise
        """
        return True if instance and \
                       instance.state_code in cls.__USED_STATE_CODES else False


class AutoScalingGroup(EC2BaseResource):
    pass


class LaunchConfiguration(EC2BaseResource):
    pass


class KeyPair(EC2BaseResource):
    pass


class ElasticIP(EC2BaseResource):
    pass
