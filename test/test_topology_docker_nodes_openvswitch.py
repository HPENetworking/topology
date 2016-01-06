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
Test suite for module topology_docker.platform.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from pynml import Node, BidirectionalPort, BidirectionalLink

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

    link1 = BidirectionalLink(identifier='link1')
    platform.add_bilink((s1, s1p1), (h1, h1p1), link1)

    link2 = BidirectionalLink(identifier='link2')
    platform.add_bilink((s1, s1p2), (s2, s2p1), link2)

    link3 = BidirectionalLink(identifier='link3')
    platform.add_bilink((s2, s2p2), (h2, h2p1), link3)

    platform.post_build()

    # Ping test
    ###########

    # Configure IP and bring UP host 1 interfaces
    commands = """
    ip link set hs1-1 up
    ip addr add 10.0.10.1/24 dev hs1-1
    ip route add default via 10.0.10.2
    """
    hs1.libs.common.assert_batch(commands)

    # Configure IP and bring UP host 2 interfaces
    commands = """
    ip link set hs2-1 up
    ip addr add 10.0.30.1/24 dev hs2-1
    ip route add default via 10.0.30.2
    """
    hs2.libs.common.assert_batch(commands)

    # Configure IP and bring UP switch 1 interfaces
    commands = """
    ip link set sw1-3 up
    ip link set sw1-4 up
    ip addr add 10.0.10.2/24 dev sw1-3
    ip addr add 10.0.20.1/24 dev sw1-4
    ip route add 10.0.30.0/24 via 10.0.20.2
    """
    sw1.libs.common.assert_batch(commands)

    # Configure IP and bring UP switch 2 interfaces
    commands = """
    ip link set sw2-3 up
    ip link set sw2-4 up
    ip addr add 10.0.20.2/24 dev sw2-3
    ip addr add 10.0.30.2/24 dev sw2-4
    ip route add 10.0.10.0/24 via 10.0.20.1
    """
    sw2.libs.common.assert_batch(commands)

    ping_result = hs1.send_command('ping -c 1 10.0.30.1')
    platform.destroy()
    assert '1 packets transmitted, 1 received' in ping_result
