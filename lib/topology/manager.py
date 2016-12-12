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
topology manager module.

This module takes care of understanding the topology defined in the test
suite, commanding its construction to appropriate topology platform plugin
and finally commanding its destruction to the plugin also.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from sys import exc_info
from copy import deepcopy
from datetime import datetime
from traceback import format_exc
from collections import OrderedDict

from six import string_types

from pynml.manager import ExtendedNMLManager

from pyszn.parser import parse_txtmeta
from .platforms.node import BaseNode
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
      all the objects in the namespace using the embedded
      :class:`pynml.manager.ExtendedNMLManager`, for example:

      ::

         mgr = TopologyManager()
         sw1 = mgr.create_node(name='My Switch 1')
         sw2 = mgr.create_node(name='My Switch 2')
         sw1p1 = mgr.create_biport(sw1)
         # ...

      See :class:`pynml.manager.ExtendedNMLManager` for more information of
      this usage.

    :param str engine: Name of the platform engine to build the topology.
     See :func:`platforms` for how to get and discover available platforms.
    """

    def __init__(self, engine=DEFAULT_PLATFORM, **kwargs):
        super(TopologyManager, self).__init__()

        if engine not in platforms():
            raise RuntimeError('Unknown platform engine "{}".'.format(engine))

        self.nml = ExtendedNMLManager(**kwargs)
        self.environment = OrderedDict()
        self.engine = engine
        self.nodes = OrderedDict()
        self.ports = OrderedDict()

        self._platform = None
        self._built = False

    def load(self, dictmeta, inject=None):
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

        :param dict dictmeta: The dictionary to load the topology from.
        :param dict inject: An attributes injection sub-dictionary as defined
         by :func:`parse_attribute_injection`.
        """
        # Load the environment
        self.environment = dictmeta.get('environment', OrderedDict())
        if inject is not None and 'environment' in inject:
            self.environment.update(inject['environment'])

        # Load nodes
        for nodes_spec in dictmeta.get('nodes', []):
            for node_id in nodes_spec['nodes']:

                # Explicitly create node
                attrs = deepcopy(nodes_spec['attributes'])
                attrs['identifier'] = node_id

                # Inject the run-specific attributes
                if inject is not None and node_id in inject['nodes']:
                    attrs.update(inject['nodes'][node_id])

                self.nml.create_node(**attrs)

        # Load ports
        for ports_spec in dictmeta.get('ports', []):
            for node_id, port in ports_spec['ports']:

                node = self.nml.get_object(node_id)

                # Explicitly create port
                attrs = deepcopy(ports_spec['attributes'])
                attrs['identifier'] = '{}-{}'.format(node_id, port)
                attrs['label'] = port

                # Inject the run-specific attributes
                if inject is not None and (node_id, port) in inject['ports']:
                    attrs.update(inject['ports'][(node_id, port)])

                self.nml.create_biport(node, **attrs)

        # Load links
        for link_spec in dictmeta.get('links', []):

            # Get endpoints
            endpoints = [None, None]
            for idx, (node_id, port) in enumerate(link_spec['endpoints']):

                # Auto-create node
                node = self.nml.get_object(node_id)

                # Auto-create biport
                port_id = '{}-{}'.format(node_id, port)
                biport = self.nml.get_object(port_id)

                # Register endpoint
                endpoints[idx] = biport

            # Explicit-create links
            attrs = deepcopy(link_spec['attributes'])

            # Inject the run-specific attributes
            if inject is not None and \
               link_spec['endpoints'] in inject['links']:
                attrs.update(inject['links'][link_spec['endpoints']])

            self.nml.create_bilink(*endpoints, **attrs)

    def parse(self, txtmeta, load=True, inject=None):
        """
        Parse a textual topology meta-description.

        For a description of the textual format see pyszn package
        documentation.

        :param str txtmeta: The textual meta-description of the topology.
        :param bool load: If ``True`` (the default) call :meth:`load`
         immediately after parse.
        :param dict inject: An attributes injection sub-dictionary as defined
         by :func:`parse_attribute_injection`.
        """
        data = parse_txtmeta(txtmeta)
        if load:
            self.load(data, inject=inject)
        return data

    def is_built(self):
        """
        Check if the current topology was built.

        :rtype: bool
        :return: True if the topology was successfully built.
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

        node_enode_map = OrderedDict()
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

                # Register engine node
                node_enode_map[node.identifier] = enode.identifier
                self.nodes[enode.identifier] = enode
                # Register empty port map
                self.ports[enode.identifier] = OrderedDict()

            stage = 'add_biport'
            for node, biport in self.nml.biports():
                eport = self._platform.add_biport(node, biport)

                # Check that engine port is of correct type
                if not isinstance(eport, string_types):
                    msg = (
                        'Platform {} returned an invalid '
                        'engine port name {}.'
                    ).format(self.engine, enode)
                    log.critical(msg)
                    raise Exception(msg)

                # Register engine port
                label = biport.metadata.get('label', biport.identifier)
                enode_id = node_enode_map[node.identifier]
                self.ports[enode_id][label] = eport

            stage = 'add_bilink'
            for node_porta, node_portb, bilink in self.nml.bilinks():
                self._platform.add_bilink(node_porta, node_portb, bilink)

            stage = 'post_build'

            # Assign the port mapping to the enode so they know their mapping
            # and be able to change it if required
            # (and globally, we do not use deepcopy).
            for enode_id, enode in self.nodes.items():
                enode.ports = self.ports[enode_id]

            self._platform.post_build()

        except:
            e = exc_info()[1]
            log.critical(
                (
                    'Build failed at stage "{}" with "{}". '
                    'Calling plugin rollback routine...'
                ).format(stage, e)
            )
            log.debug(format_exc())
            self._platform.rollback(stage, self.nodes, e)
            raise

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
        Get a platform engine with given identifier.

        :param str identifier: The node identifier.
        :rtype: A subclass of :class:`topology.platforms.node.BaseNode`
        :return: The engine node implementing the communication with the node.
        """
        return self.nodes.get(identifier, None)

    def relink(self, link_id):
        """
        Relink back a link specified in the topology.

        :param str link_id: Link identifier to be recreated.
        """
        if not self._built:
            raise RuntimeError(
                'You cannot relink on a never built topology.'
            )
        self._platform.relink(link_id)

    def unlink(self, link_id):
        """
        Unlink (break) a link specified in the topology.

        :param str link_id: Link identifier to be recreated.
        """
        if not self._built:
            raise RuntimeError(
                'You cannot unlink on a never built topology.'
            )
        self._platform.unlink(link_id)


__all__ = ['TopologyManager']
