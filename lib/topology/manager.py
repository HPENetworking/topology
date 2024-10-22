# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2024 Hewlett Packard Enterprise Development LP
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
from warnings import warn
from copy import deepcopy
from datetime import datetime
from traceback import format_exc
from collections import OrderedDict

from six import string_types
from pyszn.parser import parse_txtmeta

from .graph import TopologyGraph, Link
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
    - Set the :attr:`graph` attribute to a :class:`TopologyGraph` object. For
      example:

      ::

         from topology.graph import TopologyGraph
         from topology.manager import TopologyManager

         mgr = TopologyManager()
         graph = TopologyGraph()
         graph.add_node(Node('My Node'))
         mgr.graph = graph
         # ...

      See :class:`topology.graph.TopologyGraph` for more information of
      this usage.

    :param str engine: Name of the platform engine to build the topology.
     See :func:`platforms` for how to get and discover available platforms.
    :param dict options: Options to pass to the topology platform
    """

    def __init__(self, engine=DEFAULT_PLATFORM, options=None, **kwargs):
        super(TopologyManager, self).__init__()

        if engine not in platforms():
            raise RuntimeError('Unknown platform engine "{}".'.format(engine))

        self.graph = TopologyGraph()
        self.engine = engine
        self.options = options or OrderedDict()
        self.nodes = OrderedDict()
        self.ports = OrderedDict()

        self._platform = None
        self._built = False
        self._resolved = False

    @property
    def platform(self):
        """
        The platform object that is currently being used to build the topology.
        """
        return self._platform

    @property
    def nml(self):
        """
        Topology no longer users NML specification. This method now returns
        a :class:`topology.graph.TopologyGraph` object which was carefully
        made to have the same interface as ExtendedNMLManger used to have.

        This is obsolete and will be removed in future versions. Use the
        :attr:`graph` attribute instead.
        """
        warn(
            "nml attribute is obsolete and will be removed in future "
            "versions. Use graph attribute instead.",
            DeprecationWarning
        )
        return self.graph

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
        environment = dictmeta.get('environment', OrderedDict())
        if inject is not None and 'environment' in inject:
            environment.update(inject['environment'])

        self.graph.environment = environment

        # Load nodes
        node_to_parent = {}
        for nodes_spec in dictmeta.get('nodes', []):
            for node_id in nodes_spec['nodes']:

                # Get node attributes
                attrs = deepcopy(nodes_spec['attributes'])

                # Inject the run-specific attributes
                if inject is not None and node_id in inject['nodes']:
                    attrs.update(inject['nodes'][node_id])

                # Create a new node
                self.graph.create_node(node_id, **attrs)

                parent_id = nodes_spec['parent']
                if parent_id is not None:
                    node_to_parent[node_id] = parent_id

        # Load ports
        for ports_spec in dictmeta.get('ports', []):
            for node_id, port_label in ports_spec['ports']:

                # Create the node if still not created
                self.graph.create_node(node_id)

                # Get port attributes
                attrs = deepcopy(ports_spec['attributes'])

                # Inject the run-specific attributes
                if (
                    inject is not None and
                    (node_id, port_label) in inject['ports']
                ):
                    attrs.update(inject['ports'][(node_id, port_label)])

                # Create a new port. This call also adds the port to the
                # topology and node.
                self.graph.create_port(port_label, node_id, **attrs)

        # Load links
        for link_spec in dictmeta.get('links', []):

            # Get link attributes
            attrs = deepcopy(link_spec['attributes'])

            # Inject the run-specific attributes
            if (
                inject is not None and
                link_spec['endpoints'] in inject['links']
            ):
                attrs.update(inject['links'][link_spec['endpoints']])

            # This variable will hold these data for the link:
            # endpoints = [(node1_id, port1_label), (node2_id, port2_label)]
            endpoints = []

            for node_id, port_label in link_spec['endpoints']:

                # Create the node if it's still not created
                self.graph.create_node(node_id)

                # Create the port if it's still not created.
                self.graph.create_port(port_label, node_id)

                # Register endpoint
                endpoints.append((node_id, port_label))

            # Decompose the endpoints list into two tuples
            node1_id, port1_label = endpoints[0]
            node2_id, port2_label = endpoints[1]

            # Create a new link
            self.graph.create_link(
                node1_id, port1_label, node2_id, port2_label, **attrs
            )

        # Set parent-child relationships
        for node_id, parent_id in node_to_parent.items():
            node = self.graph.get_node(node_id)
            parent = self.graph.get_node(parent_id)

            # Set the child's parent
            node.parent = parent

            # Add the child to the parent's children
            parent.add_subnode(node)

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

    def resolve(self):
        """
        Resolve the topology.

        This method resolves the topology graph by calling the platform
        to resolve the topology. If the topology is not resolvable, the
        platform should raise an exception.
        """
        if self._built:
            raise RuntimeError(
                'You cannot resolve an already built topology.'
            )
        # Instance platform
        plugin = load_platform(self.engine)
        timestamp = datetime.now().replace(microsecond=0).isoformat()

        self._platform = plugin(
            timestamp, self.graph, **self.options
        )
        if not hasattr(self._platform, 'resolve'):
            log.warning('Platform does not implement resolve method.')
            self._resolved = True
            return

        self._platform.resolve()
        self._resolved = True

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

        if not self._resolved:
            # To keep backward compatibility, resolve the topology if it was
            # not resolved yet.
            self.resolve()

        node_enode_map = OrderedDict()

        try:
            stage = 'pre_build'
            self._platform.pre_build()

            stage = 'add_node'
            for node in self.graph.nodes():
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
            for node in self.graph.nodes():
                for port in node.ports():
                    eport = self._platform.add_biport(node, port)

                    # Check that engine port is of correct type
                    if not isinstance(eport, string_types):
                        msg = (
                            'Platform {} returned an invalid '
                            'engine port name {}.'
                        ).format(self.engine, enode)
                        log.critical(msg)
                        raise Exception(msg)

                    # Register engine port
                    label = port.metadata.get('label', port.identifier)
                    enode_id = node_enode_map[node.identifier]
                    self.ports[enode_id][label] = eport

            stage = 'add_bilink'
            for link in self.graph.links():
                node_porta = (link.node1, link.port1)
                node_portb = (link.node2, link.port2)
                self._platform.add_bilink(node_porta, node_portb, link)

            stage = 'post_build'

            # Assign the port mapping to the enode so they know their mapping
            # and be able to change it if required
            # (and globally, we do not use deepcopy).
            for enode_id, enode in self.nodes.items():
                enode.ports = self.ports[enode_id]

            self._platform.post_build()

        except (Exception, KeyboardInterrupt):
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
        Get a platform node with given identifier.

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
        warn(
            'relink() is deprecated and will be removed in future releases.'
            'Use set_link() instead.',
            DeprecationWarning
        )
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
        warn(
            'unlink() is deprecated and will be removed in future releases.'
            'Use unset_link() instead.',
            DeprecationWarning
        )
        if not self._built:
            raise RuntimeError(
                'You cannot unlink on a never built topology.'
            )
        self._platform.unlink(link_id)

    def unset_link(self, node1_id, port1_label, node2_id, port2_label):
        """
        Unset a link between two nodes.

        :param str node1_id: The first node identifier.
        :param str port1_label: The first port label.
        :param str node2_id: The second node identifier.
        :param str port2_label: The second port label.
        """
        link_id = Link.calc_id(node1_id, port1_label, node2_id, port2_label)
        self.unlink(link_id)

    def set_link(self, node1_id, port1_label, node2_id, port2_label):
        """
        Set a link between two nodes.

        :param str node1_id: The first node identifier.
        :param str port1_label: The first port label.
        :param str node2_id: The second node identifier.
        :param str port2_label: The second port label.
        """
        link_id = Link.calc_id(node1_id, port1_label, node2_id, port2_label)
        self.relink(link_id)

    def _set_test_log(self, log):
        """
        Set the current test execution log. This log is set by testlog library

        :param log: the logging object requested
        """
        for enode in self.nodes.values():
            enode._set_test_log(log)


__all__ = ['TopologyManager']
