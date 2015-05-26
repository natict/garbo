"""
...
"""
from garbo import config

from garbo.discovery.aws import ec2

__author__ = 'nati'


def main():
    config.load()
    for resource in ec2.collect_all():
        print resource  # TODO: write to garbo storage


if __name__ == '__main__':
    main()
