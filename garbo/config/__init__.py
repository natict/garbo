try:
    import ConfigParser
except ImportError:
    # noinspection PyPep8Naming
    import configparser as ConfigParser

import pkgutil

from garbo.config import aws
from garbo.config import dummy_storage

__author__ = 'nati'


def load(filename='garbo.cfg'):
    """
    Load configuration from file, overriding defaults

    :type filename: configuration file. default: garbo.cfg in current directory
    """
    # TODO: remove ugly hack
    config_modules = set([name for _, name, _ in
                          pkgutil.iter_modules(['garbo/config'])])
    config = ConfigParser.RawConfigParser()
    config.read(filename)
    for section in config.sections():
        if section in config_modules:
            for k, v in config.items(section):
                globals().get(section).__setattr__(k, v)
