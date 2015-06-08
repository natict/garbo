"""
...
"""
import logging
from garbo import config

from garbo.discovery.aws import ec2
from garbo.storage.d3js import D3JSForce

__author__ = 'nati'


def main():
    config.load()
    logging.basicConfig(level=logging.INFO)
    graph = D3JSForce()
    for item in ec2.collect_all():
        graph.add_item(item)
        # print item  # TODO: write to garbo storage
    graph.export('d3js/garbo.json')


if __name__ == '__main__':
    main()
