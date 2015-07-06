"""
    garbo AWS resources
"""

from garbo.model import AbstractResource

__author__ = 'nati'


class AWSBaseResource(AbstractResource):
    def __init__(self, region, resource_id, created=None, used=False, cleanup_candidate=True):
        rid = '/'.join((region, resource_id))
        super(AWSBaseResource, self).__init__(provider='AWS',
                                              rtype=self.__class__.__name__,
                                              rid=rid,
                                              created=created,
                                              used=used,
                                              cleanup_candidate=cleanup_candidate)

    def cleanup(self):
        # TODO: implement generic AWS cleanup method
        super(AWSBaseResource, self).cleanup()


class EBSSnapshot(AWSBaseResource):
    pass


class EBSVolume(AWSBaseResource):
    pass


class Image(AWSBaseResource):
    pass


class LoadBalancer(AWSBaseResource):
    pass


class SecurityGroup(AWSBaseResource):
    pass


class Instance(AWSBaseResource):
    # Instance state codes considered as used,
    #   see: http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    __TERMINATING_STATE_CODES = (48, )
    __RUNNING_STATE_CODES = (0, 16)

    def __init__(self, region, resource_id, created=None, used=None, cleanup_candidate=True):
        super(Instance, self).__init__(region, resource_id, created, used, cleanup_candidate)

    # TODO: rename/move, running instance doesn't indicate usage
    @classmethod
    def is_running(cls, instance):
        """
        static function to decide if an instance is running
        :param instance: boto.ec2.instance.Instance object
        :return: True if instance is running (or pending running), False otherwise
        """
        return True if instance and \
                       instance.state_code in cls.__RUNNING_STATE_CODES else False

    @classmethod
    def is_cleanup_candidate(cls, instance):
        return True if instance and \
                       instance.state_code not in cls.__TERMINATING_STATE_CODES else False


class AutoScalingGroup(AWSBaseResource):
    pass


class LaunchConfiguration(AWSBaseResource):
    pass


class KeyPair(AWSBaseResource):
    pass


class ElasticIP(AWSBaseResource):
    pass


class CacheCluster(AWSBaseResource):
    pass
