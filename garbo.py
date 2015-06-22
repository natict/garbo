"""
...
"""

import argparse
import logging

from garbo import config
from garbo.discovery.aws import ec2
from garbo.storage.dummy import dump_graph, load_graph
from garbo.storage.d3js import D3JSForce

__author__ = 'nati'


def _get_parsed_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--discovery', '-d', action='store_true', default=False,
                        help='should garbo perform a discovery, or just use stored graph')

    parser.add_argument('--gen-d3js', '-g', action='store_true', default=False,
                        help='should garbo generate a json file for D3JS Directed Force Graph')

    return parser.parse_args()


def _gen_d3js(graph):
    fdg = D3JSForce()
    for item in graph:
        fdg.add_item(item)
    fdg.export('d3js/garbo.json')


def main():
    # Load configuration and parse arguments
    config.load()
    logging.basicConfig(level=logging.INFO)
    args = _get_parsed_arguments()

    if args.discovery:
        # Perform discovery into selected storage
        graph = list(ec2.collect_all())
        dump_graph(graph)
    else:
        # Read resources and relations from storage
        graph = load_graph()

    # TODO: Read applications file

    # TODO: Perform mark & Sweep

    # Generate a graph
    if args.gen_d3js:
        _gen_d3js(graph)


if __name__ == '__main__':
    main()
