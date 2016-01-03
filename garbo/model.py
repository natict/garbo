__author__ = 'nati'


class Resource(object):
    def __init__(self, type, id, created=None, properties=None):
        super(Resource, self).__init__()
        self.type = type
        self.id = id
        self.created = created
        self.properties = properties or {}

    def __repr__(self):
        return 'Resource(type={}, id={}, created={}, properties={})'.format(
            self.type, self.id, self.created, self.properties)


class Relation(object):
    def __init__(self, src_resource, dst_resource):
        """
        :type src_resource: Resource
        :type dst_resource: Resource
        """
        super(Relation, self).__init__()
        self.src_resource = src_resource
        self.dst_resource = dst_resource

    def __repr__(self):
        return 'Relation(src_type={}, src_id={}, dst_type={}, dst_id={})'.format(
            self.src_resource.type, self.src_resource.id, self.dst_resource.type, self.dst_resource.id)