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
from os import getcwd, walk
from fnmatch import fnmatch
from logging import getLogger
from traceback import format_exc
from collections import OrderedDict
from os.path import isabs, join, abspath, isfile, basename

from six import iteritems

from .parser import parse_txtmeta, find_topology_in_python


log = getLogger(__name__)


def parse_attribute_injection(injection_file, search_paths=None):
    """
    Parses a attributes injection file into an attribute injection dictionary.

    An attribute injection file is a JSON file that specifies a list of
    injection specifications. Each specification allows to list the files to
    modify and the modifiers to apply. Each modifier specify what entities
    (devices, ports or links) will be modified and which attributes will be
    injected. The file supports wildcards and attributes matching.

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
                        "links": ["sw1:4 -- sw3:9", "rate=fast"],
                        "attributes": {
                            "rate": "slow",
                        }
                    },
                    {
                        "nodes": ["sw4"],
                        "attributes": {
                            "image": "image_for_sw4"
                        }
                    },
                    {
                        "ports": ["sw1:4"],
                        "attributes": {
                            "state": "down"
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
            '/abs/path/to/test_suite.py': {
                'sw1': {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2'
                },
                'sw3': {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2'
                }
                'sw1:4': {
                    'state': 'down'
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
    def subfolders(search_path):
        result = []
        for root, dirs, files in walk(search_path, topdown=True,
                                      followlinks=True):
            # Ignore hidden folders
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            result.extend([join(root, directory) for directory in dirs])
        return result

    paths_to_expand = list(search_paths)
    for root in paths_to_expand:
        children = subfolders(root)
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
        for filename in expand_files(spec['files'], search_paths):

            if filename not in result:
                result[filename] = OrderedDict()

            # Each specification have several "modifiers" associated to it.
            # Those modifiers hold the nodes whose attributes are to be
            # modified.
            for modifier in spec['modifiers']:
                for element_type in ['nodes', 'ports', 'links']:
                    if element_type not in modifier.keys():
                        continue
                    for element in expand_elements(
                        filename, element_type, modifier[element_type]
                    ):
                        if element not in result[filename]:
                            result[filename][element] = {}

                        for attribute, value in modifier['attributes'].items():
                            result[filename][element][attribute] = value

    log.debug('Attribute injection interpreted dictionary:')
    log.debug(result)

    return result


def expand_files(files_definitions, search_paths):
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


def expand_elements(filename, element_type, elements_definitions):
    """
    Expands a list of element definitions into the matching element names.

    A element definition is a string that can match none, one or more elements
    (by using wildcards). It can be an expression for element name matching, or
    for matching all elements that have an specific attribute value. For
    example:

    ::

        'elementa'
        'hs*'
        'type=host'

    :param str filename: A filename in which to look for matching elements.
    :param str element_type: The type of element to expand.
    :param list elements_definitions: A list of element definitions.
    :return: A list of matching elements.
    """

    expanded_elements = []

    # Grab the topology definition from a file that contains one
    log.debug('Trying to expand elements in {}'.format(filename))
    if filename.endswith('.py'):
        topology = find_topology_in_python(filename)
        if topology is None:
            log.warning((
                'Skipping element expansion for attribute injection in'
                ' filename {} in the lookup path as it does not contain a'
                ' TOPOLOGY definition.'
            ).format(filename))
            return []
    else:
        with open(filename, 'r') as fd:
            topology = fd.read().strip()
    log.debug('Found:\n{}'.format(topology))

    # Parse content
    try:
        parsed_topology = parse_txtmeta(topology)
    except:
        log.error((
            'Skipping element expansion for attribute injection in filename '
            '{} in the lookup path as SZN format parsing failed.'
        ).format(filename))
        log.debug(format_exc())
        return []

    for element_definition in elements_definitions:

        # Check if definition is for attribute matching
        if match(r'(\w+)=(\w+)', element_definition):

            # Build a dummy statement and parse it
            parsed_dummy = parse_txtmeta(
                '[{}] dummy1'.format(element_definition)
            )

            # Extract the attribute name and value
            attribute, value = list(iteritems(
                parsed_dummy[element_type][0]['attributes']
            ))[0]

            # Look for attribute name matching
            for elements_group in parsed_topology[element_type]:
                attributes = elements_group['attributes']
                if attribute in attributes and value == attributes[attribute]:

                    # Retain order, and avoid adding repeated elements
                    for element in elements_group[element_type]:
                        if element not in expanded_elements:
                            expanded_elements.append(element)
            continue

        # The definition is not attribute matching, but name matching
        for elements_group in parsed_topology[element_type]:
            for element in elements_group[element_type]:
                # FIXME: Make this prettier.
                if element_type == 'nodes':
                    pass
                elif element_type == 'ports':
                    element = '{}:{}'.format(element[0], element[1])
                elif element_type == 'links':
                    element = '{}:{} -- {}:{}'.format(
                        element[0][0], element[0][1],
                        element[1][0], element[1][1]
                    )
                else:
                    raise Exception(
                        'Unknown element type: {}'.format(element_type)
                    )
                if fnmatch(element, element_definition) and \
                        element not in expanded_elements:
                    expanded_elements.append(element)

    return expanded_elements

__all__ = [
    'parse_attribute_injection'
]
