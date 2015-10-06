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
Test suite for module topology_docker.platform.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from pynml import Node, BidirectionalPort

from topology_docker.platform import DockerPlatform


def test_ping_openvswitch():
    """
    Builds the topology described on the following schema and ping h2 from h1.

    ::

       +------+                               +------+
       |      |     +------+     +------+     |      |
       |  h1  <----->  s1  <----->  s2  <----->  h2  |
       |      |     +------+     +------+     |      |
       +------+                               +------+
    """
    # Build topology
    platform = DockerPlatform(None, None)
    platform.pre_build()

    h1 = Node(identifier='hs1', type='host')
    h2 = Node(identifier='hs2', type='host')
    s1 = Node(identifier='sw1', type='openvswitch')
    s2 = Node(identifier='sw2', type='openvswitch')

    hs1 = platform.add_node(h1)
    hs2 = platform.add_node(h2)
    sw1 = platform.add_node(s1)
    sw2 = platform.add_node(s2)

    s1p1 = BidirectionalPort(identifier='sw1-3')
    s1p2 = BidirectionalPort(identifier='sw1-4')
    platform.add_biport(s1, s1p1)
    platform.add_biport(s1, s1p2)

    s2p1 = BidirectionalPort(identifier='sw2-3')
    s2p2 = BidirectionalPort(identifier='sw2-4')
    platform.add_biport(s2, s2p1)
    platform.add_biport(s2, s2p2)

    h1p1 = BidirectionalPort(identifier='hs1-1')
    h2p1 = BidirectionalPort(identifier='hs2-1')
    platform.add_biport(h1, h1p1)
    platform.add_biport(h2, h2p1)

    platform.add_bilink((s1, s1p1), (h1, h1p1), None)
    platform.add_bilink((s1, s1p2), (s2, s2p1), None)
    platform.add_bilink((s2, s2p2), (h2, h2p1), None)

    platform.post_build()

    # Ping test
    ###########

    # Configure IP and bring UP host 1 interfaces
    hs1.send_command('ip link set hs1-1 up')
    hs1.send_command('ip addr add 10.0.10.1/24 dev hs1-1')

    # Configure IP and bring UP host 2 interfaces
    hs2.send_command('ip link set hs2-1 up')
    hs2.send_command('ip addr add 10.0.30.1/24 dev hs2-1')

    # Configure IP and bring UP switch 1 interfaces
    sw1.send_command('ip link set sw1-3 up')
    sw1.send_command('ip link set sw1-4 up')

    sw1.send_command('ip addr add 10.0.10.2/24 dev sw1-3')
    sw1.send_command('ip addr add 10.0.20.1/24 dev sw1-4')

    # Configure IP and bring UP switch 2 interfaces
    sw2.send_command('ip link set sw2-3 up')
    sw2.send_command('ip addr add 10.0.20.2/24 dev sw2-3')

    sw2.send_command('ip link set sw2-4 up')
    sw2.send_command('ip addr add 10.0.30.2/24 dev sw2-4')

    # Set static routes in switches
    sw1.send_command('ip route add 10.0.30.0/24 via 10.0.20.2')
    sw2.send_command('ip route add 10.0.10.0/24 via 10.0.20.1')

    # Set gateway in hosts
    hs1.send_command('ip route add default via 10.0.10.2')
    hs2.send_command('ip route add default via 10.0.30.2')

    ping_result = hs1.send_command('ping -c 1 10.0.30.1')
    platform.destroy()
    assert '1 packets transmitted, 1 received' in ping_result
