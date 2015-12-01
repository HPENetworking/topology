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
Test for basic switching behaviour using Ryu + Openvswitch.
Runs the simple_switch ryu application
which makes two switches behave like a single switch by forwarding packets to
the controller.
"""

import time

TOPOLOGY = """
# 			  +-------+
# 			  |       |
# 			  |  ryu  |
# 			  |       |
# 			  +-------+
#              |     |
#      +-------+     +-------+
#      |  sw1  |     |  sw2  |
#      +-------+     +-------+
#          |             |
#      +-------+     +-------+
#      |  hs1  |     |  hs2  |
#      +-------+     +-------+


# Nodes
[type=ryu name="Ryu"] ryu
[type=openvswitch name="Switch 1"] sw1
[type=openvswitch name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Ports
[ipv4="10.0.10.1/24" up=True] ryu:1
[ipv4="10.0.11.1/24" up=True] ryu:2
[ipv4="10.0.10.2/24" up=True] sw1:1
[ipv4="10.0.11.2/24" up=True] sw2:1
[up=True] sw1:2
[up=True] sw2:2

# Hosts in same network
[ipv4="192.168.0.1/24" up=True] hs1:1
[ipv4="192.168.0.2/24" up=True] hs2:1

# Links
ryu:1 -- sw1:1
ryu:2 -- sw2:1
sw1:2 -- hs1:1
sw2:2 -- hs2:1
"""


def test_controller_link(topology):

    ryu = topology.get('ryu')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    sw1 = topology.get('sw1')
    sw2 = topology.get('sw2')

    assert ryu is not None
    assert hs1 is not None
    assert hs2 is not None
    assert sw1 is not None
    assert sw2 is not None

    # ---- OVS Setup ----

    # Create a bridge
    sw1('ovs-vsctl add-br br0')
    sw2('ovs-vsctl add-br br0')

    # Bring up ovs interface
    sw1('ip link set br0 up')
    sw2('ip link set br0 up')

    # Add the front port connecting to the controller
    sw1('ovs-vsctl add-port br0 1')
    sw2('ovs-vsctl add-port br0 1')

    # Drop packets if the connection to controller fails
    sw1('ovs-vsctl set-fail-mode br0 secure')
    sw2('ovs-vsctl set-fail-mode br0 secure')

    # Remove the front port's IP address
    sw1('ifconfig 1 0 up')
    sw2('ifconfig 1 0 up')

    # Add the front port connecting to the host
    sw1('ovs-vsctl add-port br0 2')
    sw2('ovs-vsctl add-port br0 2')
    sw1('ifconfig 2 0 up')
    sw2('ifconfig 2 0 up')

    # Give the virtual switch an IP address
    sw1('ifconfig br0 10.0.10.2 netmask 255.255.255.0 up')
    sw2('ifconfig br0 10.0.11.2 netmask 255.255.255.0 up')

    # Connect to the OpenFlow controller
    sw1('ovs-vsctl set-controller br0 tcp:10.0.10.1:6633')
    sw2('ovs-vsctl set-controller br0 tcp:10.0.11.1:6633')

    # Wait for OVS to connect to controller
    time.sleep(10)

    # Assert that switches are connected to Ryu
    vsctl_sw1_show = sw1('ovs-vsctl show')
    assert 'is_connected: true' in vsctl_sw1_show

    vsctl_sw2_show = sw2('ovs-vsctl show')
    assert 'is_connected: true' in vsctl_sw2_show

    # Test simple_switch with pings between hs1 and hs2
    ping_hs2 = hs1('ping -c 1 192.168.0.2')
    assert '1 packets transmitted, 1 received' in ping_hs2

    ping_hs1 = hs2('ping -c 1 192.168.0.1')
    assert '1 packets transmitted, 1 received' in ping_hs1
