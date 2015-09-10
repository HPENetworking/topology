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
Mininet engine platform module for topology.

Topology platform plugin for Mininet.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from mininet.net import Mininet

from .base import BasePlatform, BaseNode


log = logging.getLogger(__name__)


class MininetPlatform(BasePlatform):

    def __init__(self, timestamp, nmlmanager):
        super(MininetPlatform, self).__init__(timestamp, nmlmanager)
        self._net = None
        self.nmlnode_node_map = {}

    def pre_build(self):
        self._net = Mininet()
        self._net.addController('c0')

    def add_node(self, node):
        variety = node.metadata.get('variety', 'switch')
        mininet_node = None

        if variety == 'switch':
            mininet_node = MininetSwitch(
                self._net.addSwitch(node.identifier,
                                    dpid=str(len(self.nmlnode_node_map))))
        elif variety == 'host':
            mininet_node = MininetHost(self._net.addHost(node.identifier,
                                       dpid=str(len(self.nmlnode_node_map))))
        else:
            log.error('Unsupported variety')

        self.nmlnode_node_map[node.identifier] = mininet_node
        return mininet_node

    def add_biport(self, node, biport):
        # For mininet this is not necessary
        pass

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        node_a = self.nmlnode_node_map[nodeport_a[0].identifier].node
        node_b = self.nmlnode_node_map[nodeport_b[0].identifier].node

        self._net.addLink(node_a, node_b)

    def post_build(self):
        self._net.start()

    def destroy(self):
        self._net.stop()


class MininetSwitch(BaseNode):

    def __init__(self, mininet_node):
        self.node = mininet_node

    def send_command(self, command):
        self.node.sendCmd(command)


class MininetHost(BaseNode):

    def __init__(self, mininet_node):
        self.node = mininet_node

    def send_command(self, command):
        self.node.sendCmd(command)

__all__ = ['MininetPlatform', 'MininetSwitch']
