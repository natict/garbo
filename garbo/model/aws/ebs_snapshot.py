from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class EBSSnapshot(AbstractResource):
    def __init__(self, region, snapshot_id, created=None):
        rid = '/'.join((region, snapshot_id))
        super(EBSSnapshot, self).__init__(rid=rid, created=created)

    def cleanup(self):
        # TODO
        super(EBSSnapshot, self).cleanup()
