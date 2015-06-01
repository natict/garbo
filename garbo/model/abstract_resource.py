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
