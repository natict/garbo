__author__ = 'nati'

from abc import ABCMeta


class AbstractRelation(object):
    """
    An abstract class defining an undirected relation between cloud resources
    """

    __metaclass__ = ABCMeta

    def __init__(self, *rids):
        """
        :param rids: A collection of Resource IDs, sharing some relation
        """
        self.rids = tuple(rids)
