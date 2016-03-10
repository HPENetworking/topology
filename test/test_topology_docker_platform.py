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

from topology.manager import TopologyManager
from topology_docker.platform import DockerPlatform


def test_add_port():
    """
    Add ports and uses 'ip link list' to check they exist.
    """
    platform = DockerPlatform(None, None)
    platform.pre_build()

    node1 = Node(identifier='host1', type='host')
    host1 = platform.add_node(node1)
    assert platform.nmlnode_node_map[node1.identifier] is not None

    # Add ports
    p1 = BidirectionalPort(identifier='p1')
    platform.add_biport(node1, p1)
    p2 = BidirectionalPort(identifier='p2')
    platform.add_biport(node1, p2)
    p3 = BidirectionalPort(identifier='p3')
    platform.add_biport(node1, p3)

    # Add link
    link = BidirectionalLink(identifier='link')
    platform.add_bilink((node1, p1), (node1, p2), link)

    platform.post_build()

    result = host1('ip link list')

    platform.destroy()

    assert 'p1: <BROADCAST,MULTICAST> ' in result
    assert 'p2: <BROADCAST,MULTICAST> ' in result
    assert 'p3: <BROADCAST,MULTICAST> ' in result


def test_shell():
    """
    Checks that the bash shell of a host sends a proper reply.
    """
    platform = DockerPlatform(None, None)
    platform.pre_build()

    # Add node
    node1 = Node(identifier='host1', type='host')
    host1 = platform.add_node(node1)

    # Add ports
    p1 = BidirectionalPort(identifier='p1')
    platform.add_biport(host1, p1)
    p2 = BidirectionalPort(identifier='p2')
    platform.add_biport(host1, p2)
    p3 = BidirectionalPort(identifier='p3')
    platform.add_biport(host1, p3)

    platform.post_build()

    reply = host1('echo "var"')

    platform.destroy()

    assert 'var' in reply


def test_build_topology():
    """
    Builds (and destroys) a basic topology consisting in one switch and one
    host
    """
    platform = DockerPlatform(None, None)
    platform.pre_build()

    # Create node 1
    node1 = Node(identifier='host1', type='host')
    host1 = platform.add_node(node1)
    assert platform.nmlnode_node_map[node1.identifier] is not None

    # Create node 2
    node2 = Node(identifier='host2', type='host')
    host2 = platform.add_node(node2)
    assert platform.nmlnode_node_map[node2.identifier] is not None

    # Add a port to node 1
    p1 = BidirectionalPort(identifier='p1')
    platform.add_biport(node1, p1)

    # Add a port to node 2
    p2 = BidirectionalPort(identifier='p2')
    platform.add_biport(node2, p2)

    # Create a link between both ports
    link = BidirectionalLink(identifier='link')
    platform.add_bilink((node1, p1), (node2, p2), link)

    platform.post_build()

    # Configure network
    host1('ip link set dev p1 up')
    host1('ip addr add 10.1.1.1/24 dev p1')
    host2('ip link set dev p2 up')
    host2('ip addr add 10.1.1.2/24 dev p2')

    # Test ping
    ping_result = host2('ping -c 1 10.1.1.1')

    platform.destroy()

    assert '1 packets transmitted, 1 received' in ping_result


def test_ping():
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
    s1 = Node(identifier='sw1', type='host')
    s2 = Node(identifier='sw2', type='host')

    hs1 = platform.add_node(h1)
    hs2 = platform.add_node(h2)
    sw1 = platform.add_node(s1)
    sw2 = platform.add_node(s2)

    s1p1 = BidirectionalPort(identifier='3')
    s1p2 = BidirectionalPort(identifier='4')
    platform.add_biport(s1, s1p1)
    platform.add_biport(s1, s1p2)

    s2p1 = BidirectionalPort(identifier='3')
    s2p2 = BidirectionalPort(identifier='4')
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
    hs1('ip link set dev hs1-1 up')
    hs1('ip addr add 10.0.10.1/24 dev hs1-1')

    # Configure IP and bring UP host 2 interfaces
    hs2('ip link set dev hs2-1 up')
    hs2('ip addr add 10.0.30.1/24 dev hs2-1')

    # Configure IP and bring UP switch 1 interfaces
    sw1('ip link set dev 3 up')
    sw1('ip link set dev 4 up')

    sw1('ip addr add 10.0.10.2/24 dev 3')
    sw1('ip addr add 10.0.20.1/24 dev 4')

    # Configure IP and bring UP switch 2 interfaces
    sw2('ip link set dev 3 up')
    sw2('ip addr add 10.0.20.2/24 dev 3')

    sw2('ip link set dev 4 up')
    sw2('ip addr add 10.0.30.2/24 dev 4')

    # Set static routes in switches
    sw1('ip route add 10.0.30.0/24 via 10.0.20.2')
    sw2('ip route add 10.0.10.0/24 via 10.0.20.1')

    # Set gateway in hosts
    hs1('ip route add default via 10.0.10.2')
    hs2('ip route add default via 10.0.30.2')

    ping_result = hs1('ping -c 1 10.0.30.1')
    platform.destroy()
    assert '1 packets transmitted, 1 received' in ping_result


def test_unlink_relink():
    """
    Test the unlink and relink calls.

    Creates a topology with two hosts with a port each one and a named link
    between them. During execution the link gets down and up again and the
    connection is asserted in all stages.
    """

    topology = "[identifier=thelink] hs1:a -- hs2:b"

    mgr = TopologyManager(engine='docker')
    mgr.parse(topology)
    mgr.build()

    hs1 = mgr.get('hs1')
    hs2 = mgr.get('hs2')

    try:

        assert hs1 is not None
        assert hs2 is not None

        # Configure IPs
        hs1('ip link set dev a up')
        hs1('ip addr add 10.0.15.1/24 dev a')
        hs2('ip link set dev b up')
        hs2('ip addr add 10.0.15.2/24 dev b')

        # Test connection
        ping_result = hs1('ping -c 1 10.0.15.2')
        assert '1 packets transmitted, 1 received' in ping_result

        # Unlink
        mgr.unlink('thelink')

        # Test connection
        ping_result = hs1('ping -c 1 10.0.15.2')
        assert 'Network is unreachable' in ping_result

        # Relink
        mgr.relink('thelink')

        # Test connection
        ping_result = hs1('ping -c 1 10.0.15.2')
        assert '1 packets transmitted, 1 received' in ping_result

    finally:
        mgr.unbuild()
