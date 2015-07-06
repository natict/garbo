"""
...
"""

import argparse
import logging

import yaml

from garbo import config, utils
from garbo.discovery import aws
from garbo.storage.dummy import dump_graph, load_graph
from garbo.storage.d3js import D3JSForce

__author__ = 'nati'


def _get_parsed_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--applications', '-a', default=False,
                        help='a YAML file containing the name and root resources of your application')

    parser.add_argument('--discovery', '-d', action='store_true', default=False,
                        help='should garbo perform a discovery, or just use stored graph')

    parser.add_argument('--gen-d3js', '-g', action='store_true', default=False,
                        help='should garbo generate a json file for D3JS Directed Force Graph')

    return parser.parse_args()


def _gen_d3js(graph):
    # TODO: move to d3js.py ?
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
        graph = list(aws.collect_all())
        dump_graph(graph)
    else:
        # Read resources and relations from storage
        graph = load_graph()

    unused_graph = []
    if args.applications:
        # Read applications file
        with open(args.applications) as applications_file:
            applications = yaml.load(applications_file)
        root_resources = [r for app in applications for r in applications[app]]

        # Perform mark & Sweep
        unused_graph = utils.mark_and_sweep(graph, root_resources)

    out_graph = unused_graph if args.applications else graph

    if args.gen_d3js:
        # Generate a graph
        _gen_d3js(out_graph)


if __name__ == '__main__':
    main()
