# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Hewlett Packard Enterprise Development LP <asicapi@hp.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
topology manager module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from datetime import datetime
from collections import OrderedDict

from pynml import Topology

from .platforms.base import BaseNode
from .platforms.manager import platforms


log = logging.getLogger(__name__)


class NMLManager(object):

    def __init__(self, **kwargs):
        self.root = Topology(kwargs)
        self.namespace = OrderedDict()

        self.nodes = OrderedDict()
        self.biports = OrderedDict()
        self.bilinks = OrderedDict()

    def register_object(self, obj):
        if obj.identifier in self.namespace:
            raise Exception(
                'Object already in namespace {}'.format(obj.identifier)
            )
        self.namespace[obj.identifier] = obj

    def create_node(self, **kwargs):
        node = None
        self.register_object(node)
        return node

    def create_port(self, node, **kwargs):
        biport = None
        self.register_object(biport)
        self.biports[node.identifier] = biport
        return biport

    def create_link(self, porta, portb, **kwargs):
        bilink = None
        self.register_object(bilink)
        self.bilinks[(porta.identifier, portb.identifier)] = bilink
        return bilink

    def nodes(self):
        for node in self.nodes.values():
            yield node

    def ports(self):
        for nodeid, biport in self.biports.items():
            yield (self.nodes[nodeid], biport)

    def links(self):
        for (portaid, portbid), bilink in self.bilinks.items():
            yield (self.biports[portaid], self.biports[portbid], bilink)

    def export_nml(self):
        pass


class TopologyManager(object):

    def __init__(self, engine='mininet', **kwargs):
        self.nml = NMLManager(kwargs)
        self.engine = engine
        self.nodes = OrderedDict()
        self._platform = None

    def build(self):

        plugin = platforms()[self.engine]

        timestamp = datetime.now().replace(microsecond=0).isoformat()

        self._platform = plugin(timestamp, self.nml)

        self._platform.pre_build(self.nml)

        for node in self.nml.nodes():
            enode = self._platform.add_node(node)

            # Check that engine node implements the minimum interface
            if not isinstance(enode, BaseNode):
                msg = 'Platform {} returned an invalid engine node.'.format(
                    self.engine
                )
                log.critical(msg)
                raise Exception(msg)

            self.nodes[enode.identifier] = enode

        for node, biport in self.nml.biports():
            self._platform.add_biport(node, biport)

        for node_porta, node_portb, bilink in self.nml.bilinks():
            self._platform.add_bilink(node_porta, node_portb, bilink)

        self._platform.post_build(self.nml)

    def unbuild(self):
        self._platform.destroy(self.nmlmanager)

    def get(self, identifier):
        return self.nodes[identifier]


__all__ = ['TopologyManager']
