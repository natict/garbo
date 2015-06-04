from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class LoadBalancer(AbstractResource):
    def __init__(self, region, dns_name, created=None):
        rid = '/'.join((region, dns_name))
        super(LoadBalancer, self).__init__(rid=rid, created=created)

    def cleanup(self):
        # TODO
        super(LoadBalancer, self).cleanup()
