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
Docker engine platform module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from subprocess import check_call
from shlex import split as shplit

from topology.platforms.base import BasePlatform

from .root import cmd_prefix


log = logging.getLogger(__name__)


def iface_name(node, port):
    """
    FIXME: Document.
    """
    if 'port_number' in port.metadata:
        return '{}-{}'.format(
            node.identifier,
            port.metadata['port_number']
        )
    return port.identifier


class DockerPlatform(BasePlatform):
    """
    Plugin to build a topology using Docker.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):
        from .nodes.manager import nodes

        self.nmlnode_node_map = {}
        self.available_node_types = nodes()

        # Test permissions and define privileged commands prefix
        self._cmd_prefix = cmd_prefix()

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """

    def add_node(self, node):
        """
        Add a new DockerNode.

        See :meth:`BasePlatform.add_node` for more information.
        """
        # Lookup for node of given type
        node_type = node.metadata.get('type', 'host')
        if node_type not in self.available_node_types:
            raise Exception('Unknown node type {}'.format(node_type))

        # Create instance of node type and start
        enode = self.available_node_types[node_type](
            node.identifier, **node.metadata
        )
        enode.start()

        # Register and return node
        self.nmlnode_node_map[node.identifier] = enode
        return enode

    def add_biport(self, node, biport):
        """
        Add a port to the docker node.

        See :meth:`BasePlatform.add_biport` for more information.
        """
        enode = self.nmlnode_node_map[node.identifier]
        enode.notify_add_biport(node, biport)

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        node_a, port_a = nodeport_a
        node_b, port_b = nodeport_b

        # Get enodes
        enode_a = self.nmlnode_node_map[node_a.identifier]
        enode_b = self.nmlnode_node_map[node_b.identifier]

        # Determine interfaces names
        intf_a = iface_name(node_a, port_a)
        intf_b = iface_name(node_b, port_b)

        # Create links between nodes:
        #   docs.docker.com/articles/networking/#building-a-point-to-point-connection # noqa
        command_template = """ \
            ip link add {intf_a} type veth peer name {intf_b}
            ip link set {intf_a} netns {enode_a._pid}
            ip link set {intf_b} netns {enode_b._pid}\
        """
        commands = command_template.format(**locals()).splitlines()
        for command in commands:
            check_call(shplit(
                self._cmd_prefix + command.lstrip()
            ))

        # Notify enodes of created interfaces
        enode_a.notify_add_bilink(nodeport_a, bilink)
        enode_b.notify_add_bilink(nodeport_b, bilink)

    def post_build(self):
        """
        Ports are created for each node automatically while adding links.
        Creates the rest of the ports (no-linked ports)

        See :meth:`BasePlatform.post_build` for more information.
        """
        for enode in self.nmlnode_node_map.values():
            enode.notify_post_build()

    def destroy(self):
        """
        See :meth:`BasePlatform.destroy` for more information.
        """
        for enode in self.nmlnode_node_map.values():
            enode.stop()


__all__ = ['iface_name', 'DockerPlatform']
