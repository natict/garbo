__author__ = 'nati'

from abc import ABCMeta


class AbstractRelation(object):
    """
    An abstract class defining an undirected relation between cloud resources
    """

    __metaclass__ = ABCMeta

    def __init__(self, *urids):
        """
        :param urids: A collection of Universal Resource IDs, sharing some relation
        """
        self.urids = tuple(sorted(urids))

    def __str__(self):
        return self.urids.__str__()
