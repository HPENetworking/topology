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
topology parser module.

This module takes care of parsing a topology meta-description in a Graphviz
like format.

This topology representation format allows to quickly specify simple topologies
that are only composed of simple nodes, ports and links between them. For a
more programmatic format consider the ``metadict`` format or using the
:class:`pynml.manager.ExtendedNMLManager` directly.

The format for the textual description of a topology is similar to Graphviz
syntax and allows to define nodes and ports with shared attributes and links
between two endpoints with shared attributes too.

::

    # Nodes
    [type=switch attr1=1] sw1 sw2
    hs1

    # Ports
    [speed=1000] sw1:3 sw2:3

    # Links
    [linkattr1=20] sw1:a -- sw2:a
    [linkattr2=40] sw1:3 -- sw2:3

In the above example two nodes with the attributes ``type`` and ``attr1`` are
specified. Then a third node `hs1` with no particular attributes is defined.
Later, we specify some attributes (speed) for a couple of ports. In the same
way, a link between endpoints MAY have attributes. An endpoint is a combination
of a node and a port name.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from traceback import format_exc
from collections import OrderedDict


log = logging.getLogger(__name__)


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


def build_parser():
    """
    Build a pyparsing parser for our custom topology description language.

    :rtype: pyparsing.MatchFirst
    :return: A pyparsing parser.
    """
    from pyparsing import (
        Word, Literal, QuotedString,
        StringStart, StringEnd,
        alphas, nums, alphanums,
        Group, OneOrMore, Optional
    )

    number = Word(nums)
    text = QuotedString('"')
    identifier = Word(alphas, alphanums + '_')

    attribute = (
        identifier('key') + Literal('=') +
        (text | number | identifier)('value')
    )
    attributes = (
        Literal('[') +
        OneOrMore(Group(attribute))('attributes') +
        Literal(']')
    )

    node = identifier('node')
    port = node + Literal(':') + (identifier | number)('port')
    link = port('endpoint_a') + Literal('--') + port('endpoint_b')

    nodes_spec = (
        StringStart() + Optional(attributes) +
        OneOrMore(Group(node))('nodes') + StringEnd()
    )
    ports_spec = (
        StringStart() + Optional(attributes) +
        OneOrMore(Group(port))('ports') + StringEnd()
    )
    link_spec = (
        StringStart() + Optional(attributes) +
        link('link') + StringEnd()
    )

    statement = link_spec | ports_spec | nodes_spec

    return statement


def parse_txtmeta(txtmeta):
    """
    Parse a textual description of a topology and return a dictionary of it's
    elements.

    :param str txtmeta: The textual meta-description of the topology.
    :rtype: dict
    :return: Topology as dictionary.
    """
    statement = build_parser()
    data = {
        'nodes': [],
        'ports': [],
        'links': []
    }

    def process_attributes(parsed):
        """
        Convert a pyparsing object with parsed attributes in a dictionary.
        """
        attrs = OrderedDict()

        if 'attributes' not in parsed:
            return attrs

        for attr in parsed.attributes:

            value = attr.value

            # Try to convert simple types
            try:
                value = int(value)
            except ValueError:
                pass
            if value == 'True':
                value = True
            elif value == 'False':
                value = False

            attrs[attr.key] = value
        return attrs

    for lineno, raw_line in enumerate(txtmeta.splitlines(), 1):
        try:
            # Ignore comments and empty line
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse line and optional attributes
            parsed = statement.parseString(line)
            attrs = process_attributes(parsed)
            log.debug(parsed.dump())
            log.debug(attrs)

            # Process link lines
            if 'link' in parsed:
                link = parsed.link
                data['links'].append({
                    'endpoints': (
                        (link.endpoint_a.node, link.endpoint_a.port),
                        (link.endpoint_b.node, link.endpoint_b.port),
                    ),
                    'attributes': attrs
                })
                continue

            # Process port lines
            if 'ports' in parsed:
                data['ports'].append({
                    'ports': [
                        (port.node, port.port) for port in parsed.ports
                    ],
                    'attributes': attrs
                })
                continue

            # Process port lines
            if 'nodes' in parsed:
                data['nodes'].append({
                    'nodes': [node.node for node in parsed.nodes],
                    'attributes': attrs
                })
                continue

            raise Exception('Unknown line type parsed.')

        except Exception:
            e = ParseException(lineno, raw_line, format_exc())
            log.error(str(e))
            log.debug(e.exc)
            raise e

    return data


def find_topology_in_python(filename):
    """
    Find the TOPOLOGY variable inside a Python file.

    This helper functions build a AST tree a grabs the variable from it. Thus,
    the Python code isn't executed.

    :param str filename: Path to file to search for TOPOLOGY.
    :rtype: str or None
    :return: The value of the TOPOLOGY variable if found, None otherwise.
    """
    import ast

    try:
        with open(filename) as fd:
            tree = ast.parse(fd.read())

        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Assign):
                continue
            if node.targets[0].id == 'TOPOLOGY':
                return node.value.s

    except:
        log.error(format_exc())
    return None


__all__ = [
    'ParseException',
    'parse_txtmeta',
    'find_topology_in_python'
]
