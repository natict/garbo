from garbo.model.abstract_relation import AbstractRelation
from garbo.model.abstract_resource import AbstractResource

__author__ = 'nati'


class Relation(AbstractRelation):
    """
    Undirected relation between cloud resources
    """

    def __init__(self, *urids):
        # expand resources to urids automatically
        expanded_urids = [o.urid() if isinstance(o, AbstractResource) else o for o in urids]
        super(Relation, self).__init__(*expanded_urids)
