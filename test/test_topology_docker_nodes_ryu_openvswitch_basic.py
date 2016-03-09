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
Test for basic switching behaviour using Ryu + Openvswitch.

Runs the simple_switch ryu application which makes two switches behave like a
single switch by forwarding packets to the controller.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from time import sleep
from subprocess import check_output

import pytest


TOPOLOGY = """
#             +-------+
#             |       |
#             |  ryu  |
#             |       |
#             +-------+
#                 |
#             +-------+
#             |  sw1  |
#             +-------+
#             |       |
#      +-------+     +-------+
#      |  hs1  |     |  hs2  |
#      +-------+     +-------+


# Nodes
[type=ryu name="Ryu"] ryu
[type=openvswitch name="Switch 1"] sw1
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Ports
[ipv4="10.0.10.1/24" up=True] ryu:oobm
[ipv4="10.0.10.2/24" up=True] sw1:oobm
[up=True] sw1:1
[up=True] sw1:2

# Hosts in same network
[ipv4="192.168.0.1/24" up=True] hs1:1
[ipv4="192.168.0.2/24" up=True] hs2:1

# Links
ryu:oobm -- sw1:oobm
sw1:1 -- hs1:1
sw1:2 -- hs2:1
"""


@pytest.mark.skipif(
    'openvswitch' not in check_output('lsmod').decode('utf-8'),
    reason='Requires Open vSwitch kernel module.')
def test_controller_link(topology):

    ryu = topology.get('ryu')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    sw1 = topology.get('sw1')

    assert ryu is not None
    assert hs1 is not None
    assert hs2 is not None
    assert sw1 is not None

    # ---- OVS Setup ----

    # Configuration:
    # - Create a virtual bridge
    # - Drop packets if the connection to controller fails
    # - Add frontal ports to virtual bridge
    # - Give the virtual bridge an IP address
    # - Bring up virtual bridge
    # - Connect to the OpenFlow controller
    commands = """
    ovs-vsctl add-br br0
    ovs-vsctl set-fail-mode br0 secure
    ovs-vsctl add-port br0 1
    ovs-vsctl add-port br0 2
    ip addr add 10.0.10.3/24 dev br0
    ip link set br0 up
    ovs-vsctl set-controller br0 tcp:10.0.10.1:6633
    """
    sw1.libs.common.assert_batch(commands)

    # Poll until the switch is connected to Ryu
    timeout = 10  # 10 seconds
    for i in range(timeout):
        status = sw1('ovs-vsctl show')
        if 'is_connected: true' in status:
            break
        sleep(1)
    else:
        assert False, 'Ryu controller never connected'

    # Wait for Open vSwitch
    sleep(1)

    # Test simple_switch with pings between hs1 and hs2
    ping_hs2 = hs1.libs.ping.ping(1, '192.168.0.2')
    assert ping_hs2['transmitted'] == ping_hs2['received'] == 1

    ping_hs1 = hs2.libs.ping.ping(1, '192.168.0.1')
    assert ping_hs1['transmitted'] == ping_hs1['received'] == 1
