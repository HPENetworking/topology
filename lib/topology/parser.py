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
topology parser module.

This module takes care of parsing a topology meta-description in a Graphviz
like format.

This topology representation format allows to quickly specify simple topologies
that are only composed of simple nodes and links between them. For a more
feature full format consider the ``metadict`` format or using the
:class:`pynml.manager.ExtendedNMLManager` directly.

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

In the above example two nodes with the attributes ``type`` and ``attr1`` are
specified. Then a third node `hs1` with no particular attributes is defined. In
the same way, a link between endpoints MAY have attributes.

An endpoint is a combination of a node and a port number, but the port number
is optional. If the endpoint just specifies the node (``sw1``, ``sw1:``) then
the next available port is implied.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from shlex import split as shsplit
from traceback import format_exc
from collections import OrderedDict
from string import ascii_lowercase, digits


IDENTIFIER = ascii_lowercase + digits + '_'


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


def is_identifier(raw):
    """
    Check if a string is a identifier.

    >>> is_identifier('a_abbc')
    True
    >>> is_identifier('Foo')
    False
    >>> is_identifier('1abc')
    False
    >>> is_identifier('a-abbc')
    False
    >>> is_identifier('BAR')
    False

    An identifier is any non empty string which letters are ascii
    lowercase, digits or the underscore character, but needs to start with
    a letter.
    """
    if not raw:
        return False
    if not raw[0] in ascii_lowercase:
        return False
    return all(l in IDENTIFIER for l in raw)


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

    attrs_parts = shsplit(subline.replace('[', '', 1))
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


def parse_txtmeta(txtmeta):
    """
    Parse a textual description of a topology and return a dictionary of it's
    elements.

    :param str txtmeta: The textual meta-description of the topology.
    :rtype: dict
    :return: Topology as dictionary.
    """
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

    return data


__all__ = [
    'ParseException',
    'is_identifier',
    'parse_attrs',
    'parse_nodes',
    'parse_link',
    'parse_txtmeta'
]
