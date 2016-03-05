import logging
import subprocess

import os
from garbo import config
from garbo.model import Relation, Resource
from py2neo import Graph, Node, Relationship


def load_from_entries(entities, plugin=''):
    graph = Graph(config.neo4j.uri)
    graph.delete_all()  # TODO: remove only for matching discovery plugin
    nodes, relationships = set(), set()
    for e in entities:
        if isinstance(e, Relation):
            relationships.add(e)
        elif isinstance(e, Resource):
            properties = {k: str(v) for k, v in e.properties.iteritems()}
            nodes.add(Node(e.type, _id=e.id, _created=e.created, _type=e.type, **properties))
        else:
            logging.warn('invalid entity: %s', e)

    print 'Loading {} nodes and {} relationships to Neo4J'.format(len(nodes), len(relationships))

    graph.create(*nodes)
    for r in relationships:
        src = graph.find_one(r.src_resource.type, property_key='_id', property_value=r.src_resource.id)
        dst = graph.find_one(r.dst_resource.type, property_key='_id', property_value=r.dst_resource.id)
        if src and dst:
            graph.create(Relationship(src, '{}->{}'.format(r.src_resource.type, r.dst_resource.type), dst))
        else:
            logging.warn('unable to find src/dst resources for %s', r)


# TODO: this might not be the best way to dump a neo4j graph :/

def dump_to_file(path):
    try:
        with open(path, 'w') as f:
            f.write(subprocess.check_output([config.neo4j.shell_cmd,
                                             '-host', config.neo4j.host,
                                             '-port', str(config.neo4j.shell_port),
                                             '-c', 'dump']))
    except Exception:
        logging.exception('unable to dump neo4j DB')


def load_from_file(path):
    graph = Graph(config.neo4j.uri)
    graph.delete_all()  # TODO: remove only for matching discovery plugin
    try:
        with open(path, 'r') as f, open(os.devnull) as devnull:
            subprocess.check_call([config.neo4j.shell_cmd,
                                   '-host', config.neo4j.host,
                                   '-port', str(config.neo4j.shell_port)],
                                  stdin=f,
                                  stdout=devnull)
    except Exception:
        logging.exception('unable to load neo4j DB from file')
