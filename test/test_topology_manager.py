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
Test suite for module topology.manager.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from sys import version_info
from os import system, getuid
from distutils.spawn import find_executable
from collections import OrderedDict

from pytest import mark
from deepdiff import DeepDiff

from topology.manager import TopologyManager


TOPOLOGY = """
# Nodes
[shell=vtysh] sw1 sw2
[type=host] hs1
hs2

# Links
sw1:1 -- hs1:1
sw1: -- hs1
[attr1=1] sw1:4 -- hs2
"""


def teardown_function(function):
    """
    In case something goes wrong clean up mininet state.
    """
    if getuid() != 0:
        return
    mn_exec = find_executable('mn')
    if mn_exec is not None:
        system(mn_exec + ' --clean')


def test_txtmeta_parse():
    """
    Test the txtmeta parsing feature of the TopologyManager object.
    """
    topology = TopologyManager()
    dictmeta = topology.parse(TOPOLOGY, load=False)

    expected = {
        'nodes': [
            {
                'attributes': OrderedDict([('shell', 'vtysh')]),
                'nodes': set(['sw2', 'sw1'])
            },
            {
                'attributes': OrderedDict([('type', 'host')]),
                'nodes': set(['hs1'])
            },
            {
                'attributes': OrderedDict(),
                'nodes': set(['hs2'])
            }
        ],
        'links': [
            {
                'attributes': OrderedDict(),
                'endpoints': (('sw1', 1), ('hs1', 1))
            },
            {
                'attributes': OrderedDict(),
                'endpoints': (('sw1', None), ('hs1', None))
            },
            {
                'attributes': OrderedDict([('attr1', '1')]),
                'endpoints': (('sw1', 4), ('hs2', None))
            }
        ]
    }

    ddiff = DeepDiff(dictmeta, expected)
    assert not ddiff


@mark.skipif(version_info[0] == 3, reason="Mininet does not support Python3")
@mark.skipif(getuid() != 0, reason="Mininet requires root permissions")
def test_build():
    """
    Test building and unbuilding a topology using the Mininet engine.
    """
    topology = TopologyManager(engine='mininet')

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

    mnsw1 = topology.get('sw1')

    from topology.platforms.mininet import MininetSwitch
    assert isinstance(mnsw1, MininetSwitch)

    # Ping to validate nodes and link
    ping_response = topology.get('hs1').send_command(
        'ping -c 1 ' + mnsw1._mininet_node.IP())

    # Unbuild topology
    topology.unbuild()

    assert '1 packets transmitted, 1 received' in ping_response
