from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class Image(AbstractResource):
    def __init__(self, region, image_id, created=None):
        rid = '/'.join((region, image_id))
        super(Image, self).__init__(rid=rid, created=created)

    def cleanup(self):
        # TODO
        super(Image, self).cleanup()
