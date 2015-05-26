"""
...
"""

from garbo.discovery.aws import ec2
from garbo import config

__author__ = 'nati'


def main():


    for resource in ec2.collect_all(config.aws.access_key,
                                    config.aws.aws_secret_access_key):
        print resource


if __name__ == '__main__':
    main()
