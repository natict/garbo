from collections import defaultdict
import logging

from garbo.model import AbstractResource, Relation

__author__ = 'nati'


def mark_and_sweep(graph, root_resources):
    """
    Go over a directed graph of resources, starting from given set of roots, and yield non-connected resources
    :param graph:
    :param root_resources:
    :return:
    """
    resources = {i.urid(): i for i in graph if isinstance(i, AbstractResource)}
    relations = defaultdict(set)
    for r in (i for i in graph if isinstance(i, Relation) and i.dependency):
        relations[r.source].add(r.target)
    used_resources = set()
    new_used_resources = {r for r in root_resources if r in resources}  # TODO: add newly created resources as roots

    while new_used_resources:
        used_resources |= new_used_resources
        expanded_resources = {target for urid in new_used_resources
                              for target in relations.get(urid, [])
                              if target in resources}
        new_used_resources = expanded_resources - used_resources

    # Generate a subset of the original graph containing only unused resources
    unused_resource_urids = set([r for r in resources if resources[r].cleanup_candidate]) - used_resources
    logging.info('found the following unused resources: %s', unused_resource_urids)
    unused_graph = [i for i in graph if (isinstance(i, AbstractResource) and i.urid() in unused_resource_urids) or
                    (isinstance(i, Relation) and
                     i.source in unused_resource_urids and
                     i.target in unused_resource_urids)]

    return unused_graph
