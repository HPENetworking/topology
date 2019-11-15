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
Test suite for module pyszn.parser.
"""

from collections import OrderedDict

from deepdiff import DeepDiff

from pyszn.parser import parse_txtmeta


def test_parse():
    """
    Tests parsing of a complete SZN
    """

    topology = """
    # Environment
    [virtual=none awesomeness=medium]

    # Nodes
    [shell=vtysh] sw1 sw2
    [type=host] hs1
    hs2

    # Links
    sw1:1 -- hs1:1
    [attr1=2.1e2 attr2=-2.7e-1] sw1:a -- hs1:a
    [attr1=1 attr2="lorem ipsum" attr3=(1, 3.0, "B")] sw1:4 -- hs2:a
    """

    actual = parse_txtmeta(topology)

    expected = {
        'environment': OrderedDict(
            [('virtual', 'none'), ('awesomeness', 'medium')]
        ),
        'nodes': [
            {
                'attributes': OrderedDict([('shell', 'vtysh')]),
                'nodes': ['sw1']
            },
            {
                'attributes': OrderedDict([('type', 'host')]),
                'nodes': ['hs1']
            },
            {
                'attributes': OrderedDict(),
                'nodes': ['hs2']
            },
            {
                'attributes': OrderedDict([('shell', 'vtysh')]),
                'nodes': ['sw2']
            },
        ],
        'ports': [
            {
                'ports': [('sw1', '1')],
                'attributes': OrderedDict()
            },
            {
                'ports': [('hs1', '1')],
                'attributes': OrderedDict()
            },
            {
                'ports': [('sw1', 'a')],
                'attributes': OrderedDict()
            },
            {
                'ports': [('hs1', 'a')],
                'attributes': OrderedDict()
            },
            {
                'ports': [('sw1', '4')],
                'attributes': OrderedDict()
            },
            {
                'ports': [('hs2', 'a')],
                'attributes': OrderedDict()
            },
        ],
        'links': [
            {
                'attributes': OrderedDict(),
                'endpoints': (('sw1', '1'), ('hs1', '1'))
            },
            {
                'attributes': OrderedDict(
                    [
                        ('attr1', 210.0),
                        ('attr2', -0.27)
                    ]
                ),
                'endpoints': (('sw1', 'a'), ('hs1', 'a'))
            },
            {
                'attributes': OrderedDict(
                    [
                        ('attr1', 1), ('attr2', 'lorem ipsum'),
                        ('attr3', [1, 3.0, 'B'])
                    ]
                ),
                'endpoints': (('sw1', '4'), ('hs2', 'a'))
            }
        ]
    }

    assert not DeepDiff(actual, expected)


def test_autonode():
    """
    Test the automatic creation of implicit nodes
    """

    topology = """
    sw1:port1
    """

    actual = parse_txtmeta(topology)

    expected = {
        'environment': OrderedDict(),
        'nodes': [{'attributes': OrderedDict(), 'nodes': ['sw1']}],
        'ports': [{'ports': [('sw1', 'port1')], 'attributes': OrderedDict()}],
        'links': []
    }

    assert not DeepDiff(actual, expected)


def test_multiline():
    """
    Test the support for multiline attributes
    """
    topology = """
    # Environment
    [
        virtual=none
        awesomeness=medium
        float=1.0
        list=(
            1,
            3.14,
            True
        )
    ]
    """
    actual = parse_txtmeta(topology)

    expected = {
        'environment': OrderedDict(
            [
                ('virtual', 'none'), ('awesomeness', 'medium'), ('float', 1.0),
                ('list', [1, 3.14, True])
            ]
        ),
        'nodes': [],
        'ports': [],
        'links': []
    }

    assert not DeepDiff(actual, expected)


def test_attributes():
    """
    Test that attributes should just be added to the nodes on the same line
    """
    topology = """
    [attr=value] hs1 hs3
    hs2
    """

    actual = parse_txtmeta(topology)

    expected = {
        'environment': OrderedDict(),
        'nodes': [
            {
                'attributes': OrderedDict([('attr', 'value')]),
                'nodes': ['hs1']
            },
            {
                'attributes': OrderedDict([('attr', 'value')]),
                'nodes': ['hs3']
            },
            {
                'attributes': OrderedDict(),
                'nodes': ['hs2']
            },
        ],
        'ports': [],
        'links': []
    }

    assert not DeepDiff(actual, expected)


def test_single():
    """
    Test that a single line string (no new lines '\\n') is parsed
    """
    topology = """[attr=value] hs1"""

    actual = parse_txtmeta(topology)

    expected = {
        'environment': OrderedDict(),
        'nodes': [
            {
                'attributes': OrderedDict([('attr', 'value')]),
                'nodes': ['hs1']
            },
        ],
        'ports': [],
        'links': []
    }

    assert not DeepDiff(actual, expected)
