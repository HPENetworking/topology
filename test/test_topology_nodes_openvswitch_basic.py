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
Test for basic openvswitch behavior
"""

import time

TOPOLOGY = """
#             +-------+
#             |  sw1  |
#             +-------+
#             |       |
#      +-------+     +-------+
#      |  hs1  |     |  hs2  |
#      +-------+     +-------+


# Nodes
[type=openvswitch name="Switch 1"] sw1
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Switch Ports
[up=True] sw1:1
[up=True] sw1:2

# Hosts in same network
[ipv4="192.168.0.1/24" up=True] hs1:1
[ipv4="192.168.0.2/24" up=True] hs2:1

# Links
sw1:1 -- hs1:1
sw1:2 -- hs2:1
"""


def test_controller_link(topology):

    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    sw1 = topology.get('sw1')

    assert hs1 is not None
    assert hs2 is not None
    assert sw1 is not None

    # ---- OVS Setup ----

    # Create bridge, bring up ovs interface and add the front ports
    commands = """
    ovs-vsctl add-br br0
    ip link set br0 up
    ovs-vsctl add-port br0 1
    ovs-vsctl add-port br0 2
    """
    sw1.libs.common.assert_batch(commands)

    # Wait for OVS
    time.sleep(1)

    # Ping between the hosts
    ping_hs2 = hs1('ping -c 1 192.168.0.2')
    assert '1 packets transmitted, 1 received' in ping_hs2

    ping_hs1 = hs2('ping -c 1 192.168.0.1')
    assert '1 packets transmitted, 1 received' in ping_hs1
