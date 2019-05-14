# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Hewlett Packard Enterprise Development LP
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
SZN parser module.

This module takes care of parsing a topology meta-description written in SZN.

This topology representation format allows to quickly specify simple topologies
that are only composed of simple nodes, ports and links between them. For a
more programmatic format consider the ``metadict`` format or using the
:class:`pynml.manager.ExtendedNMLManager` directly.

The format for the textual description of a topology is similar to Graphviz
syntax and allows to define nodes and ports with shared attributes and links
between two endpoints with shared attributes too.

::

    # Environment
    [kernel="3.13.0-77-generic"]

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

from copy import deepcopy
import logging
from traceback import format_exc
from collections import OrderedDict

from pyparsing import (
    Word, Literal, QuotedString,
    ParserElement, alphas, nums, alphanums,
    Group, OneOrMore, Optional,
    LineEnd, Suppress, LineStart, restOfLine, CaselessLiteral
)

log = logging.getLogger(__name__)


class ParseException(Exception):
    """
    Custom exception thrown by the parser if it was unable to parse a SZN
    string.

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

    :return: A pyparsing parser.
    :rtype: pyparsing.MatchFirst
    """
    ParserElement.setDefaultWhitespaceChars(' \t')
    nl = Suppress(LineEnd())
    number = Word(nums).setParseAction(lambda l, s, t: int(t[0]))
    boolean = (
        CaselessLiteral('true') | CaselessLiteral('false')
    ).setParseAction(lambda l, s, t: t[0].casefold() == 'true')
    comment = Literal('#') + restOfLine + nl
    text = QuotedString('"')
    identifier = Word(alphas, alphanums + '_')
    empty_line = LineStart() + LineEnd()
    attribute = Group(
        identifier('key') + Suppress(Literal('=')) +
        (text | number | boolean | identifier)('value') + Optional(nl)
    )
    attributes = (
        Suppress(Literal('[')) + Optional(nl) +
        OneOrMore(attribute) +
        Suppress(Literal(']'))
    )

    node = identifier('node')
    port = Group(node + Suppress(Literal(':')) + (identifier | number)('port'))
    link = Group(
        port('endpoint_a') + Suppress(Literal('--')) + port('endpoint_b')
    )

    environment_spec = (
        attributes + nl
    ).setResultsName('env_spec', listAllMatches=True)
    nodes_spec = (
        Group(
            Optional(attributes)('attributes') +
            Group(OneOrMore(node))('nodes')
        ) + nl
    ).setResultsName('node_spec', listAllMatches=True)
    ports_spec = (
        Group(
            Optional(attributes)('attributes') +
            Group(OneOrMore(port))('ports')
        ) + nl
    ).setResultsName('port_spec', listAllMatches=True)
    link_spec = (
        Group(
            Optional(attributes)('attributes') + link('links')
        ) + nl
    ).setResultsName('link_spec', listAllMatches=True)

    statements = OneOrMore(
        comment |
        link_spec |
        ports_spec |
        nodes_spec |
        environment_spec |
        empty_line
    )
    return statements


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
        'environment': OrderedDict(),
        'nodes': [],
        'ports': [],
        'links': [],
    }

    parsed_result = statement.parseString(txtmeta)

    # Process environment line
    if 'env_spec' in parsed_result:
        if len(parsed_result['env_spec']) > 1:
            raise Exception(
                'Multiple declaration of environment attributes: '
                '{}'.format(parsed_result['env_spec'][1])
            )
        for attr in parsed_result['env_spec'][0]:
            data['environment'][attr.key] = attr.value

    # Process the links
    if 'link_spec' in parsed_result:
        for parsed in parsed_result['link_spec']:
            link = parsed[0].links
            attrs = OrderedDict()
            if "attributes" in parsed[0]:
                for attr in parsed[0].attributes:
                    attrs[attr.key] = attr.value
            data['links'].append({
                'endpoints': (
                    (str(link.endpoint_a.node), str(link.endpoint_a.port)),
                    (str(link.endpoint_b.node), str(link.endpoint_b.port)),
                ),
                'attributes': attrs,
            })

            data['nodes'].append({
                'nodes': [
                    str(link.endpoint_a.node), str(link.endpoint_b.node)
                ],
                'attributes': OrderedDict(),
            })
            data['ports'].append({
                'ports': [
                    (str(link.endpoint_a.node), str(link.endpoint_a.port)),
                    (str(link.endpoint_b.node), str(link.endpoint_b.port))
                ],
                'attributes': OrderedDict(),
            })

    # Process the ports
    if 'port_spec' in parsed_result:
        for parsed in parsed_result['port_spec']:
            ports = parsed[0].ports
            attrs = OrderedDict()
            if "attributes" in parsed[0]:
                for attr in parsed[0].attributes:
                    attrs[attr.key] = attr.value
            data['ports'].append({
                'ports': [
                    (str(port.node), str(port.port)) for port in ports
                ],
                'attributes': attrs,
            })
            data['nodes'].append({
                'nodes': [str(port.node) for port in ports],
                'attributes': OrderedDict(),
            })

    # Process the nodes
    if 'node_spec' in parsed_result:
        for parsed in parsed_result['node_spec']:
            nodes = parsed[0].nodes
            attrs = OrderedDict()
            if "attributes" in parsed[0]:
                for attr in parsed[0].attributes:
                    attrs[attr.key] = attr.value
            data['nodes'].append({
                'nodes': [str(node) for node in nodes],
                'attributes': attrs,
            })

    # Remove duplicate data created implicitly
    temp_nodes = OrderedDict()
    for node_list in data['nodes']:
        for node in node_list['nodes']:
            if node not in temp_nodes.keys():
                temp_nodes[node] = deepcopy(node_list['attributes'])
            else:
                temp_nodes[node].update(node_list['attributes'])

    temp_ports = OrderedDict()
    for port_list in data['ports']:
        for port in port_list['ports']:
            if port not in temp_ports.keys():
                temp_ports[port] = deepcopy(port_list['attributes'])
            else:
                temp_ports[port].update(port_list['attributes'])

    data['nodes'] = [
        {'nodes': [k], 'attributes': v} for k, v in temp_nodes.items()
    ]

    data['ports'] = [
        {'ports': [k], 'attributes': v} for k, v in temp_ports.items()
    ]
    return data


def find_topology_in_python(filename):
    """
    Find the TOPOLOGY variable inside a Python file.

    This helper functions build a AST tree a grabs the variable from it. Thus,
    the Python code isn't executed.

    :param str filename: Path to file to search for TOPOLOGY.

    :return: The value of the TOPOLOGY variable if found, None otherwise.
    :rtype: str or None
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

    except Exception:
        log.error(format_exc())
    return None


__all__ = [
    'ParseException',
    'parse_txtmeta',
    'find_topology_in_python'
]
