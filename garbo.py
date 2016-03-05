#!/usr/bin/env python2.7

import glob
import logging
import time

import click as click
import os
from garbo import config
from garbo.discovery import aws
from garbo.storage import neo4j

__author__ = 'nati'


@click.group()
@click.option('--debug-level', help='e.g. info', default='warn')
def cli(debug_level):
    logging.basicConfig(level=debug_level.upper())
    config.load()


@cli.command(help='re-discover the graph from AWS')
def discover():
    neo4j.load_from_entries(aws.discover_all())


@cli.command(help='dump the graph to file')
@click.option('--filename', '-f', help='cypher file', default=None)
def dump(filename):
    filename = filename or 'data/dump_{}.cypher'.format(str(int(time.time())))
    neo4j.dump_to_file(filename)


@cli.command(help='load given file or newest dump')
@click.option('--filename', '-f', help='cypher file', default=None)
def load(filename):
    filename = filename or max(glob.iglob('data/dump_*.cypher'), key=os.path.getctime)
    neo4j.load_from_file(filename)


if __name__ == '__main__':
    cli()
