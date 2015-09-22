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
from datetime import datetime
from traceback import format_exc
from collections import OrderedDict
from string import ascii_lowercase, digits

from pynml.manager import ExtendedNMLManager

from .platforms.base import BaseNode
from .platforms.manager import platforms


log = logging.getLogger(__name__)


IDENTIFIER = ascii_lowercase + digits + '_'


class ParseException(Exception):
    """
    Custom exception thrown by the parser if it could succeded.

    :var lineno: Line number of the parsing error.
    :var raw_line: Raw line that failed to be parsed.
    :var exc: Internal failure traceback of the parser.
    """
    def __init__(self, lineno, raw_line, exc):
        super(ParseException, self).__init__(
            'Unable to parse line #{}: "{}"'.format(
                lineno, raw_line
            )
        )
        self.lineno = lineno
        self.raw_line = raw_line
        self.exc = exc


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

    def __init__(self, engine='mininet', **kwargs):
        self.nml = ExtendedNMLManager(**kwargs)
        self.engine = engine
        self.nodes = OrderedDict()
        self._platform = None

    def is_identifier(self, raw):
        """
        Check if a string is a identifier.

        An identifier is any non empty string which letters are ascii
        lowercase, digits or the underscore character, but needs to start with
        a letter.
        """
        if not raw:
            return False
        if not raw[0] in ascii_lowercase:
            return False
        return all(l in IDENTIFIER for l in raw)

    def load(self, dictmeta):
        """
        FIXME write some documentation.

        FIXME actualy read the dictmeta and load the topology
        FIXME Specify dictionary format
        """
        print('*' * 79)
        print(dictmeta)

        # Load nodes
        for nodes_spec in dictmeta.get('nodes', []):
            attributes = nodes_spec['attributes']
            for node_id in nodes_spec['nodes']:
                self.nml.create_node(identifier=node_id, **attributes)

    def parse(self, txtmeta, load=True):
        """
        Parse a textual topology meta-description.

        This topology representation format allows to quickly specify simple
        topologies that are only composed of simple nodes and links between
        them. For a more feature full format consider the ``metadict`` format
        or using the :class:`pynml.manager.ExtendedNMLManager` directly.

        The format for the textual description of a topology is similar to
        Graphviz syntax and allows to define nodes with shared attributes and
        links between endpoints with shared attributes too.

        ::

            # Nodes
            [type=switch attr1=1] sw1 sw2
            hs1

            # Links
            [linkattr1=20] sw1 -- sw2
            [linkattr2=40] sw1: -- sw2:3

        In the above example two nodes with the attributes ``type`` and
        ``attr1`` are specified. Then a third node `hs1` with no particular
        attributes is defined. In the same way, a link between endpoints MAY
        have attributes.

        An endpoint is a combination of a node and a port number, but the
        port number is optional. If the endpoint just specifies the node
        (``sw1``, ``sw1:``) then the next available port is implied.
        """

        def parse_attrs(subline, raw_line, lineno):
            """
            Parse all attributes in a subline:

            ::

                '[myattr1="A String" myattr2=bar' ->
                {
                    'myattr1': '"A String"'
                    'myattr2': 'bar'
                }
            """
            attrs = OrderedDict()

            attrs_parts = subline.replace('[', '', 1).split()
            for part in attrs_parts:

                key, value = [p.strip() for p in part.split('=')]

                # Check for value overriding
                if key in attrs:
                    log.warning(
                        'Repeated key in line #{}: "{}"'.format(
                            lineno, raw_line
                        )
                    )
                    log.warning(
                        'Overriding "{}" value from "{}" to "{}"'.format(
                            key, attrs[key], value
                        )
                    )

                attrs[key] = value

            return attrs

        def parse_nodes(line, raw_line, lineno):
            """
            Parse a nodes description:

            ::

                '[...] sw1 hs1' ->
                {
                    'nodes': ('sw1', 'hs1'),
                    'attributes': {
                        ...
                    }
                }
            """
            attributes = OrderedDict()
            nodes_part = line

            # Parse attributes if present
            if ']' in line:
                attrs_part, nodes_part = line.split(']')
                attributes = parse_attrs(attrs_part, raw_line, lineno)

            nodes = nodes_part.split()
            nodes_set = set(nodes)

            if len(nodes) != len(nodes_set):
                log.warning(
                    'Repeated node names in line #{}: "{}"'.format(
                        lineno, raw_line
                    )
                )

            return {
                'nodes': nodes_set,
                'attributes': attributes
            }

        def parse_link(line, raw_line, lineno):
            """
            Parse a link description:

            ::

                '[...] sw1:1 -- hs1:1' ->
                {
                    'endpoints': (('sw1', 1), ('hs1', 1)),
                    'attributes': {
                        ...
                    }
                }

                '[...] sw1: -- hs1' ->
                {
                    'endpoints': (('sw1', None), ('hs1', None)),
                    'attributes': {
                        ...
                    }
                }
            """
            attributes = OrderedDict()
            link_part = line

            # Parse attributes if present
            if ']' in line:
                attrs_part, link_part = line.split(']')
                attributes = parse_attrs(attrs_part, raw_line, lineno)

            # Split endpoints
            endp_a, endp_b = link_part.split('--')
            endpoints = []

            # Parse endpoints
            for endp in [endp_a, endp_b]:

                endp = endp.strip()
                node_port = endp.split(':')

                # Check consistency
                if len(node_port) not in [1, 2] or not node_port[0]:
                    msg = 'Bad link specification at line #{}: "{}"'.format(
                        lineno, raw_line
                    )
                    log.error(msg)
                    raise Exception(msg)

                # First syntax 'sw1'
                if len(node_port) == 1:
                    node_port.append(None)

                # Second syntax 'sw1:'
                elif not node_port[1]:
                    node_port[1] = None

                # Third syntax 'sw:1'
                else:
                    node_port[1] = int(node_port[1])

                endpoints.append(tuple(node_port))

            return {
                'endpoints': tuple(endpoints),
                'attributes': attributes
            }

        # Parse txtmeta
        data = {
            'nodes': [],
            'links': []
        }

        for lineno, raw_line in enumerate(txtmeta.splitlines(), 1):

            try:

                # Ignore comments and empty line
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue

                # Parse links
                if '--' in line:
                    link_spec = parse_link(line, raw_line, lineno)
                    data['links'].append(link_spec)
                    log.debug('Line number {}:\n{}'.format(lineno, link_spec))
                    continue

                # Parse nodes
                nodes_spec = parse_nodes(line, raw_line, lineno)
                data['nodes'].append(nodes_spec)
                log.debug('Line number {}:\n{}'.format(lineno, nodes_spec))
                continue
            except Exception:
                e = ParseException(lineno, raw_line, format_exc())
                log.error(str(e))
                log.debug(e.exc)
                raise e

        if load:
            self.load(data)

        return data

    def build(self):
        """
        Build the topology hold by this manager.

        This method instance the platform engine and request the build of the
        topology defined.
        """
        timestamp = datetime.now().replace(microsecond=0).isoformat()

        # Instance platform
        plugin = platforms()[self.engine]
        self._platform = plugin(timestamp, self.nml)

        self._platform.pre_build()

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

        self._platform.post_build()

    def unbuild(self):
        """
        Undo the topology.

        This removes all references to the engine nodes and request the
        platform to destroy the topology.
        """
        if self._platform is None:
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


__all__ = ['ParseException', 'TopologyManager']
