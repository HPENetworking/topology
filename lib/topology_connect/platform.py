# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
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
topology_connect engine platform module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from logging import getLogger
from collections import OrderedDict

from topology.platforms.base import BasePlatform
from topology.platforms.utils import NodeLoader

from .node import ConnectNode


log = getLogger(__name__)


class ConnectPlatform(BasePlatform):
    """
    FIXME: Document.
    """

    def __init__(self, timestamp, nmlmanager):

        self.node_loader = NodeLoader(
            'connect', api_version='1.0', base_class=ConnectNode
        )

        self.nmlnode_node_map = OrderedDict()
        self.available_node_types = self.node_loader.load_nodes()

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """

    def add_node(self, node):
        """
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
        See :meth:`BasePlatform.add_biport` for more information.
        """
        # FIXME: Save this port for later validation in post_build.
        return biport.identifier

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        # FIXME: Save this link for later validation in post_build.

    def post_build(self):
        """
        See :meth:`BasePlatform.post_build` for more information.
        """
        # FIXME: Check that the final topology is the same as the known /
        # hardwired one.

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
        log.info('Topology Connect rollback called...')
        self.destroy()

    def relink(self, link_id):
        """
        See :meth:`BasePlatform.relink` for more information.
        """
        raise RuntimeError(
            'relink is not currently supported in this Engine Platform.'
        )

    def unlink(self, link_id):
        """
        See :meth:`BasePlatform.unlink` for more information.
        """
        raise RuntimeError(
            'unlink is not currently supported in this Engine Platform.'
        )


__all__ = ['ConnectPlatform']
