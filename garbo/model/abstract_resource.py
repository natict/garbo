__author__ = 'nati'

from abc import ABCMeta, abstractmethod, abstractproperty


class AbstractResource(object):
    """
    A cloud resource abstract class
    """

    __metaclass__ = ABCMeta

    def __init__(self, rid):
        """
        :param rid: Resource ID, should be the same across multiple discovery
                      engines
        """
        self.rid = rid

    @abstractproperty
    def used(self):
        """
        Used components are in the core of a GC operation, as they and all
          their dependencies must be preserved.

        Different resources might have different definitions of being used,
          and different users might define usage differently.

        :return: True if a resource is being used, False otherwise
        """
        pass

    @abstractproperty
    def seen(self):
        """
        :return: Resource last seen time (via a discovery service)
        """
        pass

    @abstractproperty
    def created(self):
        """
        :return: Resource creation time
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Perform a resource cleanup.

        Users can define their own cleanup functions for sending reports, and
          adding an additional user-intervention layer (eg. Hubot)

        :return:
        """
        pass
