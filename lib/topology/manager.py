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

This module takes care of understanding the topology defined in the test
suite, commanding its construction to appropriate topology platform plugin
and finally commanding its destruction to the plugin also.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from copy import deepcopy
from datetime import datetime
from traceback import format_exc
from collections import OrderedDict

from pynml.manager import ExtendedNMLManager

from .parser import parse_txtmeta
from .platforms.base import BaseNode
from .platforms.manager import platforms, load_platform, DEFAULT_PLATFORM


log = logging.getLogger(__name__)


class TopologyManager(object):
    """
    Main Topology Manager object.

    This object is responsible to build a topology given a description.

    There is three options to build a topology:

    - Using the simplified textual description using a Graphviz like syntax.
      To use this option call the :meth:`parse`.
    - Using a basic Python dictionary to load the description of the topology.
      To use this option call the :meth:`load`.
    - Build a full NML topology using NML objects and relations and register
      all the objects in the namespace using the enbbedded
      :class:`pynml.manager.ExtendedNMLManager`, for example:

      ::

         mgr = TopologyManager()
         sw1 = mgr.create_node(name='My Switch 1')
         sw2 = mgr.create_node(name='My Switch 2')
         sw1p1 = mgr.create_biport(sw1)
         # ...

      See :class:`pynml.manager.ExtendedNMLManager` for more information of
      this usage.

    :param str engine: Name of the engine platform to build the topology.
     See :func:`platforms` for how to get and discover available platforms.
    """

    def __init__(self, engine=DEFAULT_PLATFORM, **kwargs):

        if engine not in platforms():
            raise RuntimeError('Unknown platform engine "{}".'.format(engine))

        self.nml = ExtendedNMLManager(**kwargs)
        self.engine = engine
        self.nodes = OrderedDict()
        self._platform = None
        self._built = False

    def load(self, dictmeta):
        """
        Load a topology description in a dictionary format.

        Dictionary format:

        ::

            {
                'nodes': [
                    {
                        'nodes': ['sw1', 'hs1', ...],
                        'attributes': {...}
                    },
                ],
                'ports': [
                    {
                        'ports': [('sw1', '1'), ('hs1', '1'), ...],
                        'attributes': {...}
                    }
                ]
                'links': [
                    {
                        'endpoints': (('sw1', '1'), ('hs1', '1')),
                        'attributes': {...}
                    },
                ]
            }

        See also the module :mod:`topology.parser`.

        :param dict dictmeta: The dictionary to load the topology from.
        """
        autoports = {}

        def next_autoport(node_id):
            """
            Get the next port available.
            """
            if node_id not in autoports:
                return 1
            node_autoports = autoports[node_id]
            bottom = min(node_autoports) + 1
            while bottom in node_autoports:
                bottom += 1
            return bottom

        def add_port_attrs(node_id, port, attrs):
            """
            Determine a biport attributes in a multitude of scenarios.
            """
            # Auto port
            if port is None:
                if 'port_number' not in attrs:
                    attrs['port_number'] = next_autoport(node_id)
                port = attrs['port_number']

            # Add port_number if missing
            elif 'port_number' not in attrs:
                try:
                    attrs['port_number'] = int(port)
                except ValueError:
                    pass

            # Register port number if exists
            if 'port_number' in attrs:
                port_number = attrs['port_number']
                if node_id not in autoports:
                    autoports[node_id] = []
                if port_number in autoports[node_id]:
                    raise RuntimeError(
                        'Port #{} for {} was already assigned'.format(
                            port_number, node_id
                        )
                    )
                autoports[node_id].append(port_number)

            # Set identifier
            attrs['identifier'] = '{}-{}'.format(node_id, port)

        # Load nodes
        for nodes_spec in dictmeta.get('nodes', []):
            for node_id in nodes_spec['nodes']:

                # Explicit-create node
                attrs = deepcopy(nodes_spec['attributes'])
                attrs['identifier'] = node_id
                self.nml.create_node(**attrs)

        # Load ports
        for ports_spec in dictmeta.get('ports', []):
            for node_id, port in ports_spec['ports']:

                # Auto-create nodes
                node = self.nml.get_object(node_id)
                if node is None:
                    node = self.nml.create_node(identifier=node_id)

                # Explicit-create port
                attrs = deepcopy(ports_spec['attributes'])
                add_port_attrs(node_id, port, attrs)
                self.nml.create_biport(node, **attrs)

        # Load links
        for link_spec in dictmeta.get('links', []):

            # Get or create biports
            endpoints = [None, None]
            for idx, (node_id, port) in enumerate(link_spec['endpoints']):

                # Auto-create nodes
                node = self.nml.get_object(node_id)
                if node is None:
                    node = self.nml.create_node(identifier=node_id)

                # Autoport
                biport = None
                if port is not None:
                    identifier = '{}-{}'.format(node_id, port)
                    biport = self.nml.get_object(identifier)

                if biport is None:
                    attrs = {}
                    add_port_attrs(node_id, port, attrs)
                    biport = self.nml.create_biport(node, **attrs)

                # Register endpoint
                endpoints[idx] = biport

            # Explicit-create links
            attrs = deepcopy(link_spec['attributes'])
            self.nml.create_bilink(*endpoints, **attrs)

    def parse(self, txtmeta, load=True):
        """
        Parse a textual topology meta-description.

        For a description of the textual format see the module
        :mod:`topology.parser`.
        """
        data = parse_txtmeta(txtmeta)
        if load:
            self.load(data)
        return data

    def is_built(self):
        """
        Check if the current topology was built.

        :rtype: bool
        :return: True if the topology was succesfully built.
        """
        return self._built

    def build(self):
        """
        Build the topology hold by this manager.

        This method instance the platform engine and request the build of the
        topology defined.
        """
        if self._built:
            raise RuntimeError(
                'You cannot build a topology twice.'
            )

        timestamp = datetime.now().replace(microsecond=0).isoformat()
        stage = 'instance'

        # Instance platform
        plugin = load_platform(self.engine)
        self._platform = plugin(timestamp, self.nml)

        try:
            stage = 'pre_build'
            self._platform.pre_build()

            stage = 'add_node'
            for node in self.nml.nodes():
                enode = self._platform.add_node(node)

                # Check that engine node implements the minimum interface
                if not isinstance(enode, BaseNode):
                    msg = (
                        'Platform {} returned an invalid '
                        'engine node {}.'
                    ).format(self.engine, enode)
                    log.critical(msg)
                    raise Exception(msg)

                self.nodes[enode.identifier] = enode

            stage = 'add_biport'
            for node, biport in self.nml.biports():
                self._platform.add_biport(node, biport)

            stage = 'add_bilink'
            for node_porta, node_portb, bilink in self.nml.bilinks():
                self._platform.add_bilink(node_porta, node_portb, bilink)

            stage = 'post_build'
            self._platform.post_build()

        except Exception as e:
            log.critical(
                (
                    'Build failed at stage "{}" with "{}". '
                    'Calling plugin rollback routine...'
                ).format(stage, e)
            )
            log.debug(format_exc())
            self._platform.rollback(stage, self.nodes, e)
            raise e

        self._built = True

    def unbuild(self):
        """
        Undo the topology.

        This removes all references to the engine nodes and request the
        platform to destroy the topology.
        """
        if not self._built:
            raise RuntimeError(
                'You cannot unbuild and never built topology.'
            )

        # Remove own reference to enodes
        self.nodes = OrderedDict()

        # Call platform destroy hook
        self._platform.destroy()

        # Explicitly delete platform
        del self._platform
        self._platform = None

    def get(self, identifier):
        """
        Get a engine platform with given identifier.

        :param str identifier: The node identifier.
        :rtype: A subclass of :class:`topology.platforms.base.BaseNode`
        :return: The engine node implementing the communication with the node.
        """
        return self.nodes.get(identifier, None)


__all__ = ['TopologyManager']
