# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Hewlett Packard Enterprise Development LP
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

from re import match
from glob import glob
from json import loads
from os import getcwd, walk
from fnmatch import fnmatch
from logging import getLogger
from traceback import format_exc
from collections import OrderedDict
from os.path import isabs, join, abspath, isfile, basename


from pyszn.parser import parse_txtmeta, find_topology_in_python

log = getLogger(__name__)


def parse_attribute_injection(injection_file, search_paths=None):
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
    :param list search_paths: Paths to search for files when the file match is
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
    # Define search paths
    if search_paths is None:
        search_paths = [abspath(getcwd())]
    log.debug('Injection search paths: {}'.format(search_paths))

    # Expand search paths recursively to include all subfolders
    paths_to_expand = list(search_paths)
    for root in paths_to_expand:
        children = _subfolders(root)
        search_paths.extend(children)

    # Make search paths unique
    uniques = []
    for path in search_paths:
        if path not in uniques:
            uniques.append(path)
    search_paths = uniques
    log.debug('Expanded injection search paths: {}'.format(search_paths))

    # Read injection file
    with open(injection_file) as fd:
        injection_spec = loads(fd.read())

    result = OrderedDict()

    # Iterate all specifications, expand files and fill return dictionary
    for spec in injection_spec:
        for filename in _expand_files(spec['files'], search_paths):

            if filename not in result:
                result[filename] = {}
                result[filename]['environment'] = {}
                result[filename]['nodes'] = OrderedDict()
                result[filename]['ports'] = OrderedDict()
                result[filename]['links'] = OrderedDict()

            # Environment attributes are parsed from the spec
            try:
                for attribute, value in spec['environment'].items():
                    result[filename]['environment'][attribute] = value
            except KeyError:
                pass
            # Each specification have several "modifiers" associated to it.
            # Those modifiers hold the nodes whose attributes are to be
            # modified.
            for modifier in spec['modifiers']:

                # Nodes
                if 'nodes' in modifier:
                    for node in _expand_nodes(filename, modifier['nodes']):
                        if node not in result[filename]['nodes']:
                            result[filename]['nodes'][node] = {}

                        for attribute, value in modifier[
                                'attributes'].items():
                            result[filename]['nodes'][node][
                                attribute] = value

                # Ports
                if 'ports' in modifier:
                    for port in _expand_ports(
                            filename, _port_str_to_tuple(modifier['ports'])):
                        if port not in result[filename]['ports']:
                            result[filename]['ports'][port] = {}

                        for attribute, value in modifier[
                                'attributes'].items():
                            result[filename]['ports'][port][
                                attribute] = value

                # Links
                if 'links' in modifier:
                    for link in _expand_links(
                            filename, _link_str_to_tuple(modifier['links'])):
                        if link not in result[filename]['links']:
                            result[filename]['links'][link] = {}

                        for attribute, value in modifier[
                                'attributes'].items():
                            result[filename]['links'][link][
                                attribute] = value

    log.debug('Attribute injection interpreted dictionary:')
    log.debug(result)

    return result


def _subfolders(search_path):
    result = []
    for root, dirs, files in walk(search_path, topdown=True, followlinks=True):
        # Ignore hidden folders
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        result.extend([join(root, directory) for directory in dirs])
    return result


def _port_str_to_tuple(port_str_list):
    result = []
    for port in port_str_list:
        if not match(r'(.*)=(.*)', port):
            port_host, port_num = port.split(':')
            result.append((port_host, port_num))
        else:
            result.append(port)
    return result


def _link_str_to_tuple(link_str_list):
    result = []
    for link in link_str_list:
        if not match(r'(.*)=(.*)', link):
            link = link.replace(' ', '')
            endpoint1, endpoint2 = link.split('--')
            link1_host, link1_port = endpoint1.split(':')
            link2_host, link2_port = endpoint2.split(':')
            result.append(((link1_host, link1_port), (link2_host, link2_port)))
        else:
            result.append(link)
    return result


def _expand_files(files_definitions, search_paths):
    """
    Expands a list of files definitions into the matching files paths.

    A file definition is a string that can match none, one or more files
    (by using wildcards). It can be an absolute path, or a relative path from
    the search paths. For example:

    ::

        '/abs/path/to/my*_thing.py'
        'myfile.szn'
        'relative/test_*.py'

    :param list files_definitions: A list of files definitions.
    :param str search_paths: Paths to search for files when the file definition
     is relative.
    :return: A list of files paths.
    """

    expanded_files = []

    for file_definition in files_definitions:

        # File definitions to look for
        lookups = []

        # Determine if suite must be located in suites search path
        if isabs(file_definition):
            lookups.append(file_definition)
        else:
            for search_path in search_paths:
                lookups.append(join(search_path, file_definition))

        # Find all file matches for the suite definition
        matches = []
        for lookup in lookups:
            for filepath in glob(lookup):
                filename = basename(filepath)

                if filepath in expanded_files or not isfile(filepath):
                    continue

                if fnmatch(filename, 'test_*.py') or \
                        fnmatch(filename, '*.szn'):
                    matches.append(filepath)

        expanded_files.extend(matches)

    return expanded_files


def _expand_nodes(filename, nodes_definitions):
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

    # Grab the topology definition from a file that contains one
    log.debug('Trying to expand nodes in {}'.format(filename))
    if filename.endswith('.py'):
        topology = find_topology_in_python(filename)
        if topology is None:
            log.warning(
                ('Skipping node expansion for attribute injection in filename '
                 '{} in the lookup path as it does not contain a TOPOLOGY '
                 'definition.').format(filename))
            return []
    else:
        with open(filename, 'r') as fd:
            topology = fd.read().strip()
    log.debug('Found:\n{}'.format(topology))

    # Parse content
    try:
        parsed_topology = parse_txtmeta(topology)
    except Exception:
        log.error(
            ('Skipping node expansion for attribute injection in filename '
             '{} in the lookup path as SZN format parsing failed.'
             ).format(filename))
        log.debug(format_exc())
        return []

    for node_definition in nodes_definitions:

        # Check if definition is for attribute matching
        if match(r'(.*)=(.*)', node_definition):
            expanded_nodes.extend(
                _match_by_attr(node_definition, parsed_topology, 'nodes'))
            continue

        # The definition is not attribute matching, but name matching
        for nodes_group in parsed_topology['nodes']:
            for node in nodes_group['nodes']:
                if fnmatch(node, node_definition) and \
                        node not in expanded_nodes:
                    expanded_nodes.append(node)

    return expanded_nodes


def _match_by_attr(regex, parsed_topology, kind):
    ''' Searches a parsed topology for attributes that matcha regex.


    :param str regex: The regex to match the attribute, must of
                      the form (attribute_regex)=(value_regex).
    :param topology parsed_topology: A topology already parsed to search
                                   for matches.
    :param str kind: The kind of object that posses the attribute to search for
                     can be either 'nodes', 'ports' or 'links'.
    :return: A list of matching nodes,ports or links containing the attribute.

'''

    matched_objects = []
    regex_attribute, regex_value = regex.split('=')

    # Look for attribute name matching
    for group in parsed_topology[kind]:
        attributes = group['attributes']
        for key in attributes:
            if match(regex_attribute, key) and match(regex_value,
                                                     attributes[key]):

                # Retain order, and avoid adding repeated nodes
                for found_obj in group[kind]:
                    if found_obj not in matched_objects:
                        matched_objects.append(found_obj)

    return matched_objects


def _expand_ports(filename, ports_definitions):
    """
    Expands a list of port definitions into the matching port names.

    A port definition is a string that can match none, one or more ports
    (by using wildcards). It can be an expression for port name matching, or
    for matching all ports that have an specific attribute value. For example:

    ::

        'nodea:1'
        'hs*:1*'
        'attr=1'

    :param str filename: A filename in which to look for matching ports.
    :param list ports_definitions: A list of port definitions.
    :return: A list of matching ports.
    """
    expanded_ports = []

    # Grab the topology definition from a file that contains one
    log.debug('Trying to expand ports in {}'.format(filename))
    if filename.endswith('.py'):
        topology = find_topology_in_python(filename)
        if topology is None:
            log.warning(
                ('Skipping port expansion for attribute injection in filename '
                 '{} in the lookup path as it does not contain a TOPOLOGY '
                 'definition.').format(filename))
            return []
    else:
        with open(filename, 'r') as fd:
            topology = fd.read().strip()
    log.debug('Found:\n{}'.format(topology))

    # Parse content
    try:
        parsed_topology = parse_txtmeta(topology)
    except Exception:
        log.error(
            ('Skipping port expansion for attribute injection in filename '
             '{} in the lookup path as SZN format parsing failed.'
             ).format(filename))
        log.debug(format_exc())
        return []

    for port_definition in ports_definitions:

        # Check if definition is for attribute matching
        if type(port_definition) is not tuple:
            expanded_ports.extend(
                _match_by_attr(port_definition, parsed_topology, 'ports'))
            continue

        # The definition is not attribute matching, but name matching
        for port_group in parsed_topology['ports']:
            for port in port_group['ports']:
                if fnmatch(port[0], port_definition[0]) and fnmatch(
                        port[1],
                        port_definition[1]) and port not in expanded_ports:
                    expanded_ports.append(port)

    return expanded_ports


def _expand_links(filename, links_definitions):
    """
    Expands a list of links definitions into the matching link names.

    A link definition is a string that can match none, one or more nodes
    (by using wildcards). It can be an expression for link name matching, or
    for matching all links that have an specific attribute value. For example:

    ::

        'nodea:1 -- nodeb:1'
        'node*:1 -- nodeb:12*'
        'attr=2'

    :param str filename: A filename in which to look for matching links.
    :param list link_definitions: A list of link definitions.
    :return: A list of matching links.
    """

    expanded_links = []

    # Grab the topology definition from a file that contains one
    log.debug('Trying to expand links in {}'.format(filename))
    if filename.endswith('.py'):
        topology = find_topology_in_python(filename)
        if topology is None:
            log.warning(
                ('Skipping link expansion for attribute injection in filename '
                 '{} in the lookup path as it does not contain a TOPOLOGY '
                 'definition.').format(filename))
            return []
    else:
        with open(filename, 'r') as fd:
            topology = fd.read().strip()
    log.debug('Found:\n{}'.format(topology))

    # Parse content
    try:
        parsed_topology = parse_txtmeta(topology)
    except Exception:
        log.error(
            ('Skipping link expansion for attribute injection in filename '
             '{} in the lookup path as SZN format parsing failed.'
             ).format(filename))
        log.debug(format_exc())
        return []

    for link_definition in links_definitions:

        # Check if definition is for attribute matching
        if type(link_definition) is not tuple:
            expanded_links.extend(
                _match_by_attr(link_definition, parsed_topology, 'links'))
            continue

        # The definition is not attribute matching, but name matching
        for link_group in parsed_topology['links']:
            link = link_group['endpoints']
            if fnmatch(link[0][0], link_definition[0][0]) and fnmatch(
                    link[0][1], link_definition[0][1]) and fnmatch(
                        link[1][0], link_definition[1][0]) and fnmatch(
                            link[1][1], link_definition[1]
                            [1]) and link not in expanded_links:
                expanded_links.append(link)

    return expanded_links


__all__ = ['parse_attribute_injection']
