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
VLAN test for the P4 switch node. Tests the SAI API and switch behavior
by setting up two VLANS in a small network.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import time
from subprocess import check_output

import pytest


TOPOLOGY = """
#        +-------+         +-------+
#        |  sw1  |---------|  sw2  |
#        +-------+         +-------+
#        |    |               |    |
# +-------+ +-------+   +-------+ +-------+
# |  hs1  | |  hs2  |   |  hs3  | |  hs4  |
# +-------+ +-------+   +-------+ +-------+

# Nodes
[type=openvswitch name="Switch 1"] sw1
[type=openvswitch name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2
[type=host name="Host 1"] hs3
[type=host name="Host 2"] hs4

# Ports
[up=True] sw1:1
[up=True] sw1:2
[up=True] sw1:3
[up=True] sw2:1
[up=True] sw2:2
[up=True] sw2:3
[ipv4="192.168.0.1/24" up=True] hs1:1
[ipv4="192.168.0.2/24" up=True] hs2:1
[ipv4="192.168.0.3/24" up=True] hs3:1
[ipv4="192.168.0.4/24" up=True] hs4:1

# Links
sw1:1 -- hs1:1
sw1:2 -- hs2:1
sw2:1 -- hs3:1
sw2:2 -- hs4:1
sw1:3 -- sw2:3
"""


@pytest.mark.skipif(
    'openvswitch' not in check_output('lsmod').decode('utf-8'),
    reason='Requires Open vSwitch kernel module.')
def test_ping(topology):

    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    hs3 = topology.get('hs3')
    hs4 = topology.get('hs4')
    sw1 = topology.get('sw1')
    sw2 = topology.get('sw2')

    assert hs1 is not None
    assert hs2 is not None
    assert hs3 is not None
    assert hs4 is not None
    assert sw1 is not None
    assert sw2 is not None

    # ---- OVS Setup ----

    # Create a bridge, up ovs interface, add the front ports
    commands = """
    ovs-vsctl add-br br0
    ip link set br0 up
    ovs-vsctl add-port br0 1 tag=100
    ovs-vsctl add-port br0 2 tag=200
    ovs-vsctl add-port br0 3
    """
    sw1.libs.common.assert_batch(commands)
    sw2.libs.common.assert_batch(commands)

    # Wait for OVS
    time.sleep(1)

    # Ping between the hosts
    # Should work, hosts are in same VLAN
    ping_hs1_to_hs3 = hs1.libs.ping.ping(1, '192.168.0.3')
    assert ping_hs1_to_hs3['transmitted'] == ping_hs1_to_hs3['received'] == 1

    # Should not work, different VLANs
    ping_hs1_to_hs4 = hs1.libs.ping.ping(1, '192.168.0.4')
    assert ping_hs1_to_hs4['transmitted'] == 1
    assert ping_hs1_to_hs4['received'] == 0

    # Should work, hosts are in same VLAN
    ping_hs2_to_hs4 = hs2.libs.ping.ping(1, '192.168.0.4')
    assert ping_hs2_to_hs4['transmitted'] == ping_hs2_to_hs4['received'] == 1

    # Should not work, different VLANs
    ping_hs2_to_hs3 = hs2.libs.ping.ping(1, '192.168.0.3')
    assert ping_hs2_to_hs3['transmitted'] == 1
    assert ping_hs2_to_hs3['received'] == 0
