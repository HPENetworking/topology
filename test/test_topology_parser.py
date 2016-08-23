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
Test suite for the module topology.parser
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from collections import OrderedDict

from deepdiff import DeepDiff

from topology.parser import parse_txtmeta

TOPOLOGY = """
# Nodes
[shell=vtysh] sw1 sw2
[type=host] hs1
hs2

# Ports
sw2:9
[state=down] sw1:1
[state=up] hs1:a sw2:4

# Links
sw1:1 -- hs1:1
[rate=fast type=good] sw1:a -- hs1:a
[rate=slow] sw1:4 -- hs2:a sw2:5 -- hs2:5
"""


def test_parse_txtmeta():
    """
    Test the parsing of a SZN string into a dictionary.
    """
    actual = parse_txtmeta(TOPOLOGY)

    expected = {
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
        'ports': [
            {
                'attributes': OrderedDict(),
                'ports': [('sw2', '9')]
            },
            {
                'attributes': OrderedDict([('state', 'down')]),
                'ports': [('sw1', '1')]
            },
            {
                'attributes': OrderedDict([('state', 'up')]),
                'ports': [('hs1', 'a'), ('sw2', '4')]
            }
        ],
        'links': [
            {
                'attributes': OrderedDict(),
                'links': [(('sw1', '1'), ('hs1', '1'))]
            },
            {
                'attributes': OrderedDict(
                    [('rate', 'fast'), ('type', 'good')]
                ),
                'links': [(('sw1', 'a'), ('hs1', 'a'))]
            },
            {
                'attributes': OrderedDict([('rate', 'slow')]),
                'links': [
                    (('sw1', '4'), ('hs2', 'a')), (('sw2', '5'), ('hs2', '5'))
                ]
            }
        ]
    }

    ddiff = DeepDiff(actual, expected)
    assert not ddiff
