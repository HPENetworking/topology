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

import pytest  # noqa
from deepdiff import DeepDiff

# Reload module to properly measure coverage
from six.moves import reload_module

import topology.platforms.manager
from topology.manager import TopologyManager

reload_module(topology.platforms.manager)

TOPOLOGY = """
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
    topology = TopologyManager(engine='debug')
    dictmeta = topology.parse(TOPOLOGY, load=False)

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


def test_build():
    """
    Test building and unbuilding a topology using the Mininet engine.
    """
    topology = TopologyManager(engine='debug')

    # Create topology using the NMLManager
    sw1 = topology.nml.create_node(identifier='sw1', name='My Switch 1')
    hs1 = topology.nml.create_node(identifier='hs1', name='My Host 1',
                                   type='host')

    sw1p1 = topology.nml.create_biport(sw1)
    sw1p2 = topology.nml.create_biport(sw1)
    sw1p3 = topology.nml.create_biport(sw1)  # noqa
    hs1p1 = topology.nml.create_biport(hs1)
    hs1p2 = topology.nml.create_biport(hs1)
    hs1p3 = topology.nml.create_biport(hs1)  # noqa

    sw1p1_hs1p1 = topology.nml.create_bilink(sw1p1, hs1p1)  # noqa
    sw1p2_hs1p2 = topology.nml.create_bilink(sw1p2, hs1p2)  # noqa

    # Build topology
    topology.build()

    # Get an engine node
    assert topology.get('sw1') is not None
    assert topology.get('hs1') is not None

    # Unbuild topology
    topology.unbuild()


def test_autoport():
    """
    Test the autoport feature.
    """
    topodesc = """
        [port_number=5] hs1:oobm
        hs1:a -- hs2:x
        hs1:2 -- hs2:2
        hs1:4 -- hs2:4
        hs1:b -- hs2:y
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    assert topology.get('hs1') is not None
    assert topology.get('hs2') is not None

    ports = {k: dict(v) for k, v in topology.ports.items()}
    expected = {
        'hs1': {
            'oobm': 'oobm',
            'a': 'a',
            '2': '2',
            '4': '4',
            'b': 'b',
        },
        'hs2': {
            'x': 'x',
            '2': '2',
            '4': '4',
            'y': 'y',
        }
    }

    topology.unbuild()

    ddiff = DeepDiff(ports, expected)
    assert not ddiff
