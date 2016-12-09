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
Test suite for module topology.manager.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from collections import OrderedDict

from deepdiff import DeepDiff

from pyszn.parser import parse_txtmeta


TOPOLOGY = """
# Environment
[virtual=none awesomeness=medium]

# Nodes
[shell=vtysh] sw1 sw2
[type=host] hs1
hs2

# Links
sw1:1 -- hs1:1
sw1:a -- hs1:a
[attr1=1] sw1:4 -- hs2:a
"""


def test_txtmeta_parse():
    """
    Test the txtmeta parsing feature of the TopologyManager object.
    """
    dictmeta = parse_txtmeta(TOPOLOGY)

    expected = {
        'environment': OrderedDict(
            [('virtual', 'none'), ('awesomeness', 'medium')]
        ),
        'nodes': [
            {
                'attributes': OrderedDict([('shell', 'vtysh')]),
                'nodes': ['sw1', 'sw2']
            },
            {
                'attributes': OrderedDict([('type', 'host')]),
                'nodes': ['hs1']
            },
            {
                'attributes': OrderedDict(),
                'nodes': ['hs2']
            }
        ],
        'ports': [],
        'links': [
            {
                'attributes': OrderedDict(),
                'endpoints': (('sw1', '1'), ('hs1', '1'))
            },
            {
                'attributes': OrderedDict(),
                'endpoints': (('sw1', 'a'), ('hs1', 'a'))
            },
            {
                'attributes': OrderedDict([('attr1', 1)]),
                'endpoints': (('sw1', '4'), ('hs2', 'a'))
            }
        ]
    }

    ddiff = DeepDiff(dictmeta, expected)
    assert not ddiff
