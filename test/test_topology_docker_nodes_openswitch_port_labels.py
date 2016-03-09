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
OpenSwitch Test for vlan related configurations.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from time import sleep


TOPOLOGY = """
# +-------+                    +-------+
# |       |     +--------+     |       |
# |  hs1  <----->  ops1  <----->  hs2  |
# |       |     +--------+     |       |
# +-------+                    +-------+

# Nodes
[type=openswitch name="OpenSwitch 1"] ops1
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:if01 -- ops1:if01
ops1:IF02 -- hs2:if01
"""


def test_topology_nodes_openvswitch_port_labels(topology):
    ops1 = topology.get('ops1')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    assert ops1 is not None
    assert hs1 is not None
    assert hs2 is not None

    ops1('configure terminal')
    ops1('interface ' + str(ops1.ports['if01']))
    ops1('no shutdown')
    ops1('end')
    sleep(5)
    result = ops1('show interface ' + str(ops1.ports['if01']))
    assert result != '% Unknown command.'
