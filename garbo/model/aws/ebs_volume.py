from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class EBSVolume(AbstractResource):
    def __init__(self, region, volume_id, created=None):
        rid = '/'.join((region, volume_id))
        super(EBSVolume, self).__init__(rid=rid, created=created)

    def cleanup(self):
        # TODO
        super(EBSVolume, self).cleanup()
