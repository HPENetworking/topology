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
    """
    Plugin to build a topology on Mininet.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):
        super(MininetPlatform, self).__init__(timestamp, nmlmanager)
        self._net = None
        self.nmlnode_node_map = {}

    def pre_build(self):
        """
        Brings up a mininet instance.

        Mininet needs a controller to make a topology works.

        See :meth:`BasePlatform.pre_build` for more information.
        """
        self._net = Mininet()
        self._net.addController(b'c0')

    def add_node(self, node):
        """
        Add new switch or host node.

        See :meth:`BasePlatform.add_node` for more information.
        """
        variant = node.metadata.get('variant', 'switch')
        mininet_node = None

        if variant == 'switch':
            mininet_node = MininetSwitch(
                self._net.addSwitch(str(node.identifier),
                                    dpid=str(len(self.nmlnode_node_map))))
        elif variant == 'host':
            mininet_node = MininetHost(
                self._net.addHost(str(node.identifier),
                                  dpid=str(len(self.nmlnode_node_map))))
        else:
            log.error('Unsupported variant')

        self.nmlnode_node_map[node.identifier] = mininet_node
        return mininet_node

    def add_biport(self, node, biport):
        """
        For mininet this is not necessary.

        See :meth:`BasePlatform.add_biport` for more information.
        """
        pass

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes, ignores the port.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        node_a = self.nmlnode_node_map[nodeport_a[0].identifier].node
        node_b = self.nmlnode_node_map[nodeport_b[0].identifier].node

        self._net.addLink(node_a, node_b)

    def post_build(self):
        """
        Starts the mininet platform.

        See :meth:`BasePlatform.post_build` for more information.
        """
        self._net.start()

    def destroy(self):
        """
        Stops the mininet platform.

        See :meth:`BasePlatform.destroy` for more information.
        """
        self._net.stop()


class MininetNode(BaseNode):
    """
    Mininet Engine Node for Topology.

    This is an adaptator class for between Topology's
    :class:`topology.platforms.base.BaseNode` and Mininet's
    :class:`mininet.node.Node`.

    :param mininet_node: The node as a Mininet object.
    :type mininet_node: :class:`mininet.node.Node`
    """
    def __init__(self, mininet_node):
        self.node = mininet_node

    def send_command(self, command, shell=None):
        """
        Implementation of the ``send_command`` interface.

        See :meth:`topology.platforms.base.BaseNode.send_command` for more
        information.
        """
        if shell is not None:
            raise Exception(
                'Shell {} is not supported for mininet.'.format(shell)
            )
        return self.node.cmd(command)

    def send_data(self, data, function=None):
        """
        Implementation of the ``send_data`` interface.

        See :meth:`topology.platforms.base.BaseNode.send_data` for more
        information.
        """
        raise Exception('Unsupported interface')


class MininetSwitch(MininetNode):
    """
    Specilized class for node of type switch.

    See :class:`MininetNode`.
    """
    pass


class MininetHost(MininetNode):
    """
    Specilized class for node of type host.

    See :class:`MininetNode`.
    """
    pass

__all__ = ['MininetPlatform', 'MininetSwitch', 'MininetHost']
