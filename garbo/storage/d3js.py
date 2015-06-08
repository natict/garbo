import json
import logging
from garbo.model import Relation, AbstractResource
from garbo.model.aws.ec2 import Instance

__author__ = 'nati'

# TODO: support more resource types
# TODO: remove static types


class D3JSForce(object):
    def __init__(self):
        self.nodes = []
        self.links = []
        super(D3JSForce, self).__init__()

    def add_item(self, item):
        if isinstance(item, AbstractResource):
            self.nodes.append(item)
        elif isinstance(item, Relation):
            self.links.append(item)
        else:
            logging.warn('unable to add item, not a valid resource or relation')

    def export(self, filename):
        # convert to D3JSForce
        nodes = [{"name": str(n), "group": D3JSForce.to_group(n)} for n in self.nodes]
        nodes_dict = {nd.get('name'): i for i, nd in enumerate(nodes)}
        links = [{"source": nodes_dict.get(l.source),
                  "target": nodes_dict.get(l.target),
                  "value": 1} for l in self.links]
        with open(filename, 'wb') as file_out:
            json.dump({"nodes": nodes, "links": links}, file_out, indent=2)

    TYPE_TO_GROUP = ['SecurityGroup', 'LoadBalancer', 'EBSVolume', 'EBSSnapshot', 'Image', 'ElasticIP',
                     'KeyPair', 'LaunchConfiguration', 'AutoScalingGroup']

    @classmethod
    def to_group(cls, item):
        item_type = str(item).split(':')[0]
        if isinstance(item, Instance) and item.used:
            return 0
        elif isinstance(item, Instance):
            return 1
        else:
            return D3JSForce.TYPE_TO_GROUP.index(item_type) + 2
