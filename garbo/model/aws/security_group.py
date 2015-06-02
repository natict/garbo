from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class SecurityGroup(AbstractResource):
    def __init__(self, region, group_id, created=None):
        rid = '/'.join((region, group_id))
        super(SecurityGroup, self).__init__(rid=rid, created=created)

    def cleanup(self):
        # TODO
        super(SecurityGroup, self).cleanup()
