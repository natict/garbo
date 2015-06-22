"""
    Dummy storage- store garbo resources and relations in a pickle file
"""

import logging
import os
import pickle

from garbo import config

__author__ = 'nati'


def _graph_file():
    return os.path.join(config.dummy_storage.working_dir, config.dummy_storage.graph_filename)


def dump_graph(graph):
    graph = list(graph)  # if graph is a generator, get all the resources/relation
    try:
        with open(_graph_file(), 'w') as graph_file:
            pickle.dump(graph, graph_file)
        logging.info('exported pickled graph to %s', _graph_file())
    except Exception:
        logging.exception('unable to dump graph to file')


def load_graph():
    graph = []
    try:
        with open(_graph_file()) as graph_file:
            graph = pickle.load(graph_file)
        logging.info('loaded pickled graph from %s', _graph_file())
    except Exception:
        logging.exception('unable to load graph from file')
    return graph
