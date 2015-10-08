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
from collections import OrderedDict

from topology.platforms.base import BasePlatform

from .utils import tmp_iface, privileged_cmd
from .nodes.manager import nodes


log = logging.getLogger(__name__)


class DockerPlatform(BasePlatform):
    """
    Plugin to build a topology using Docker.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):

        self.nmlnode_node_map = OrderedDict()
        self.nmlbiport_iface_map = OrderedDict()
        self.available_node_types = nodes()

        # Create netns folder
        privileged_cmd('mkdir -p /var/run/netns')

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

        # Install container netns locally
        privileged_cmd(
            'ln -s /proc/{pid}/ns/net /var/run/netns/{pid}',
            pid=enode._pid
        )

        # Register and return node
        self.nmlnode_node_map[node.identifier] = enode
        return enode

    def add_biport(self, node, biport):
        """
        Add a port to the docker node.

        See :meth:`BasePlatform.add_biport` for more information.
        """
        enode = self.nmlnode_node_map[node.identifier]
        eport = enode.notify_add_biport(node, biport)

        # Register this port for later creation
        self.nmlbiport_iface_map[biport.identifier] = {
            'created': False,
            'iface': eport,
            'netns': enode._pid
        }

        return eport

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

        # Determine temporal interfaces names
        tmp_iface_a = tmp_iface()
        tmp_iface_b = tmp_iface()

        # Determine final interface names
        iface_a = self.nmlbiport_iface_map[port_a.identifier]['iface']
        iface_b = self.nmlbiport_iface_map[port_b.identifier]['iface']

        # Create links between nodes:
        #   docs.docker.com/articles/networking/#building-a-point-to-point-connection # noqa
        commands = """\
        ip link add {tmp_iface_a} type veth peer name {tmp_iface_b}
        ip link set {tmp_iface_a} netns {enode_a._pid}
        ip link set {tmp_iface_b} netns {enode_b._pid}
        ip netns exec {enode_a._pid} ip link set {tmp_iface_a} name {iface_a}
        ip netns exec {enode_b._pid} ip link set {tmp_iface_b} name {iface_b}\
        """
        privileged_cmd(commands, **locals())

        # Notify enodes of created interfaces
        enode_a.notify_add_bilink(nodeport_a, bilink)
        enode_b.notify_add_bilink(nodeport_b, bilink)

        # Mark interfaces as created
        self.nmlbiport_iface_map[port_a.identifier]['created'] = True
        self.nmlbiport_iface_map[port_b.identifier]['created'] = True

    def post_build(self):
        """
        Ports are created for each node automatically while adding links.
        Creates the rest of the ports (no-linked ports)

        See :meth:`BasePlatform.post_build` for more information.
        """
        # Create remaining interfaces
        cmd_tpl = 'ip netns exec {netns} ip tuntap add dev {iface} mode tap'
        for port_spec in self.nmlbiport_iface_map.values():

            # Ignore already created interfaces
            if port_spec['created']:
                continue

            # Create port as dummy tuntap device
            privileged_cmd(cmd_tpl, **port_spec)

            # Mark as created
            port_spec['created'] = True

        # Notify nodes of the post_build event
        for enode in self.nmlnode_node_map.values():
            enode.notify_post_build()

    def destroy(self):
        """
        See :meth:`BasePlatform.destroy` for more information.
        """
        for enode in self.nmlnode_node_map.values():
            enode.stop()

    def rollback(self, stage, enodes, exception):
        """
        See :meth:`BasePlatform.rollback` for more information.
        """
        self.destroy()


__all__ = ['DockerPlatform']
