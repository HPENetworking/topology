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

from pynml import NMLManager

from .platforms.base import BaseNode
from .platforms.manager import platforms


log = logging.getLogger(__name__)


class TopologyManager(object):

    def __init__(self, engine='mininet', **kwargs):
        self.nml = NMLManager(kwargs)
        self.engine = engine
        self.nodes = OrderedDict()
        self._platform = None

    def load(self, dictmeta):
        # FIXME actualy read the dictmeta and load the topology
        print(dictmeta)

    def parse(self, txtmeta):
        data = {
            'nodes': {},
            'ports': {},
            'links': {},
        }

        def parse_attrs(subline):
            attrs = {}

            attrs_parts = subline.replace('[', '', 1).split(',')
            for part in attrs_parts:
                key, value = part.split('=')
                attrs[key.strip()] = value.strip()

            return attrs

        def parse_node(line):
            attrs_part, nodes_part = line.split(']')

            nodes = set(nodes_part.split())
            attrs = parse_attrs(attrs_part)

            return nodes, attrs

        def parse_link(line):

            attrs = {}
            link_part = line

            if ']' in line:
                attrs_part, link_part = line.split(']')
                attrs = parse_attrs(attrs_part)

            endp_a, endp_b = link_part.split('--')
            link = []

            for endp in [endp_a, endp_b]:

                endp = endp.strip()
                node_port = endp.split(':')

                if len(node_port) not in [1, 2]:
                    raise Exception(
                        'Bad link specification: "{}"'.format(line)
                    )
                if len(node_port) == 1:
                    # FIXME: Find next suitable port number
                    node_port.append(None)

                link.append(tuple(node_port))

            return link, attrs

        for line in txtmeta.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '--' in line:
                # FIXME actualy put them in the data dict
                print(parse_link(line))
                continue

            if ']' in line:
                # FIXME actualy put them in the data dict
                print(parse_node(line))
                continue

            raise Exception('Bad topology specification: "{}"'.format(line))

        self.load(data)

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
