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
Parser attributes injection files.

This module defines a set of functions that implement logic to parse a
attributes injection file and extract from it the injection specification that
allows to modify attributes of entities in different topologies.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from re import match
from glob import glob
from json import loads
from os import getcwd
from fnmatch import fnmatch
from collections import OrderedDict
from os.path import isabs, join, abspath, isfile, basename

from six import iteritems

from .parser import parse_txtmeta, find_topology_in_python


def parse_attribute_injection(injection_file, search_path=None):
    """
    Parses a attributes injection file into an attribute injection dictionary.

    An attribute injection file is a JSON file that specifies a list of
    injection specifications. Each specification allows to list the files to
    modify and the modifiers to apply. Each modifier specify what entities
    (devices, ports or links) will be modified and which attributes will be
    injected. The file support willcards and attributes matching.

    The file format is as follows:

    ::

        [
            {
                "files": ["pathto/*", "another/foo*.py"],
                "modifiers": [
                    {
                        "nodes": ["sw1", "type=host", "sw3"],
                        "attributes": {
                            "image": "image_for_sw1_sw3_hs1_hs2",
                            "hardware": "hardware_for_sw1_sw3_hs1_hs2"
                        }
                    },
                    {
                        "nodes": ["sw4"],
                        "attributes": {
                            "image": "image_for_sw4"
                        }
                    },
                    ... # More modifiers
                ]
            },
            ... # More injection specifications
        ]

    :param str injection_file: Path for the attribute injection file.
    :param str search_path: Path to search for files when the file match is
     relative in the injection file.
     If ``None`` (the default), the current working directory is used.
    :return: An ordered dictionary with the attributes to inject of the form:

     ::

        {
            '/abs/path/to/suite.py': {
                'sw1': {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2'
                },
                'sw3': {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2'
                }
            }
        }

    :rtype: `collections.OrderedDict`
    """
    if search_path is None:
        search_path = abspath(getcwd())

    with open(injection_file) as fd:
        injection_spec = loads(fd.read())

    result = OrderedDict()

    # Iterate all specifications, expand files and fill return dictionary
    for spec in injection_spec:
        for filename in expand_files(spec['files'], search_path):

            if filename not in result:
                result[filename] = OrderedDict()

            # Each specification have several "modifiers" associated to it.
            # Those modifiers hold the nodes whose attributes are to be
            # modified.
            for modifier in spec['modifiers']:
                for node in expand_nodes(filename, modifier['nodes']):

                    if node not in result[filename]:
                        result[filename][node] = {}

                    for attribute, value in modifier['attributes'].items():
                        result[filename][node][attribute] = value

    return result


def expand_files(files_definitions, search_path):
    """
    Expands a list of files definitions into the matching files paths.

    A file definition is a string that can match none, one or more files
    (by using wildcards). It can be an absolute path, or a relative path from
    the search path. For example:

    ::

        '/abs/path/to/my*_thing.py'
        'myfile.topology'
        'relative/test_*.py'

    :param list files_definitions: A list of files definitions.
    :param str search_path: Path to search for files when the file definition
     is relative.
    :return: A list of files paths.
    """

    expanded_files = []

    for file_definition in files_definitions:

        # Determine if suite must be located in suites search path
        if not isabs(file_definition):
            file_definition = join(search_path, file_definition)

        # Find all file matches for the suite definition

        matches = []
        for filepath in glob(file_definition):
            filename = basename(filepath)

            if filepath in expanded_files or not isfile(filepath):
                continue

            if fnmatch(filename, 'test_*.py') or \
                    fnmatch(filename, '*.topology'):
                matches.append(filepath)

        expanded_files.extend(matches)

    return expanded_files


def expand_nodes(filename, nodes_definitions):
    """
    Expands a list of node definitions into the matching node names.

    A node definition is a string that can match none, one or more nodes
    (by using wildcards). It can be an expression for node name matching, or
    for matching all nodes that have an specific attribute value. For example:

    ::

        'nodea'
        'hs*'
        'type=host'

    :param str filename: A filename in which to look for matching nodes.
    :param list nodes_definitions: A list of node definitions.
    :return: A list of matching nodes.
    """

    expanded_nodes = []

    # Grab the TOPOLOGY constant from a file that defines a topology.
    topology = find_topology_in_python(filename)
    parsed_topology = parse_txtmeta(topology)

    for node_definition in nodes_definitions:

        # Check if definition is for attribute matching
        if match(r'(\w+)=(\w+)', node_definition):

            # Build a dummy statement and parse it
            parsed_dummy = parse_txtmeta(
                '[{}] dummy1'.format(node_definition)
            )
            # Extract the attribute name and value
            attribute, value = list(iteritems(
                parsed_dummy['nodes'][0]['attributes']
            ))[0]

            # Look for attribute name matching
            for nodes_group in parsed_topology['nodes']:
                if attribute in nodes_group['attributes']:

                    # Retain order, and avoid adding repeated nodes
                    for node in nodes_group['nodes']:
                        if node not in expanded_nodes:
                            expanded_nodes.append(node)
            continue

        # The definition is not attribute matching, but name matching
        for nodes_group in parsed_topology['nodes']:
            for node in nodes_group['nodes']:
                if fnmatch(node, node_definition) and \
                        node not in expanded_nodes:
                    expanded_nodes.append(node)

    return expanded_nodes


__all__ = [
    'parse_attribute_injection'
]
