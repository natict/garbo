from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class Instance(AbstractResource):
    def __init__(self, region, instance_id):
        rid = '/'.join((region, instance_id))
        super(Instance, self).__init__(rid)

    def used(self):
        super(Instance, self).used()

    def cleanup(self):
        super(Instance, self).cleanup()

    def seen(self):
        super(Instance, self).seen()

    def created(self):
        super(Instance, self).created()
