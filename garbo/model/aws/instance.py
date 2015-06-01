from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class Instance(AbstractResource):
    # Instance state codes considered as used,
    #   see: http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    __USED_STATE_CODES = (0, 16)

    def __init__(self, region, instance_id, created=None, used=False):
        rid = '/'.join((region, instance_id))
        super(Instance, self).__init__(rid=rid, created=created, used=used)

    def cleanup(self):
        # TODO
        super(Instance, self).cleanup()

    @classmethod
    def is_used(cls, instance):
        """
        static function to decide if an instance is running
        :param instance: boto.ec2.instance.Instance object
        :return: True if instance is running (or pending running), False otherwise
        """
        return True if instance and \
                       instance.state_code in cls.__USED_STATE_CODES else False
