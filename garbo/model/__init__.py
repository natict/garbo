"""
    Base definitions for garbo resources and relations.

    Plugins may extend these definitions to support more cloud providers
"""

__author__ = 'nati'

from abc import ABCMeta, abstractmethod


class AbstractResource(object):
    """
    A cloud resource abstract class
    """

    __metaclass__ = ABCMeta

    def __init__(self, rid, created=None, used=False):
        """
        :param rid: Resource ID, should be the same across multiple discovery engines
        :param created: When was this resource created (datetime)
        :param used: Is this resource being used
        """
        self.created = created
        self.rid = rid
        self._used = used

    """
    Used components are in the core of a GC operation, as they and all
      their dependencies must be preserved.

    Different resources might have different definitions of being used,
      and different users might define usage differently.
    """

    def urid(self):
        """
        Universal resource ID (across multiple resource types)
        :return:
        """
        return '{type}://{rid}'.format(type=self.__class__.__name__,
                                       rid=self.rid)

    def __str__(self):
        return self.urid()

    def used_getter(self):
        """
        Override this function to implement a dynamic usage validation
        :return: True if a resource is being used, False otherwise
        """
        return self._used

    used = property(used_getter)

    @abstractmethod
    def cleanup(self):
        """
        Perform a resource cleanup.

        Users can define their own cleanup functions for sending reports, and
          adding an additional user-intervention layer (eg. Hubot)

        :return:
        """
        pass


class Relation(object):
    """
    An class defining a directed relation between two cloud resources (source -> target)

    A relation might indicate dependency, or not.
    eg. instance is dependent on its security group, but a snapshot is not dependent on its source volume
    """

    def __init__(self, source, target, dependency=False):
        """
        :param source: garbo Resource
        :type source: AbstractResource
        :param target: garbo Resource
        :type target: AbstractResource
        :param dependency: True if this is a dependency relation, False otherwise
        :type dependency: bool
        """
        self.source, self.target = [o.urid() if isinstance(o, AbstractResource) else o for o in (source, target)]
        self.dependency = dependency

    def __str__(self):
        return (self.source, self.target).__str__()
