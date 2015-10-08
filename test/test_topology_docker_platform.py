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


def test_add_port():
    """
    Add ports and uses 'ip link list' to check they exist
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    hs1 = Node(identifier='hs1', type='host')
    topo_hs1 = topo.add_node(hs1)
    assert topo.nmlnode_node_map[hs1.identifier] is not None

    # Add ports
    p1 = BidirectionalPort(identifier='p1', port_number=2)
    topo.add_biport(hs1, p1)
    p2 = BidirectionalPort(identifier='p2')
    topo.add_biport(hs1, p2)
    p3 = BidirectionalPort(identifier='p3')
    topo.add_biport(hs1, p3)

    # Add link
    topo.add_bilink((hs1, p1), (hs1, p2), None)

    topo.post_build()

    result = topo_hs1.send_command('ip link list')

    topo.destroy()

    assert '2: <BROADCAST,MULTICAST> ' in result
    assert 'p2' in result
    assert 'p3' in result


def test_shell():
    """
    Checks that the bash shell of a host sends a proper reply.
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    nml_host = Node(identifier='nml_host', type='host')
    host = topo.add_node(nml_host)

    topo.post_build()

    reply = host.send_command('echo "var"')

    topo.destroy()

    assert 'var' in reply


def test_vtysh():
    """
    Checks that the vtysh shell of a host sends a proper reply.
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    nml_host = Node(
        identifier='nml_host2', type='openswitch'
    )
    host = topo.add_node(nml_host)

    topo.post_build()

    reply = host.send_command('show vlan', shell='vtysh')

    topo.destroy()

    assert 'vlan' in reply


def test_build_topology():
    """
    Builds (and destroys) a basic topology consisting in one switch and one
    host
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    hs1 = Node(identifier='hs1', type='host')
    topo_hs1 = topo.add_node(hs1)

    assert topo.nmlnode_node_map[hs1.identifier] is not None

    s1 = Node(identifier='s1', type='host')
    topo_hs2 = topo.add_node(s1)
    p1 = BidirectionalPort(identifier='p1')
    topo.add_biport(hs1, p1)

    p2 = BidirectionalPort(identifier='p2')
    topo.add_biport(s1, p2)

    topo.add_bilink((hs1, p1), (s1, p2), None)

    assert topo.nmlnode_node_map[hs1.identifier] is not None

    topo.post_build()

    topo_hs1.send_command('ifconfig p1 10.1.1.1 netmask 255.255.255.0 up')

    topo_hs2.send_command('ifconfig p2 10.1.1.2 netmask 255.255.255.0 up')

    ping_result = topo_hs2.send_command('ping -c 1 10.1.1.1')

    topo.destroy()

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
    sw1.send_command('ip link set 3 up')
    sw1.send_command('ip link set 4 up')

    sw1.send_command('ip addr add 10.0.10.2/24 dev 3')
    sw1.send_command('ip addr add 10.0.20.1/24 dev 4')

    # Configure IP and bring UP switch 2 interfaces
    sw2.send_command('ip link set 3 up')
    sw2.send_command('ip addr add 10.0.20.2/24 dev 3')

    sw2.send_command('ip link set 4 up')
    sw2.send_command('ip addr add 10.0.30.2/24 dev 4')

    # Set static routes in switches
    sw1.send_command('ip route add 10.0.30.0/24 via 10.0.20.2')
    sw2.send_command('ip route add 10.0.10.0/24 via 10.0.20.1')

    # Set gateway in hosts
    hs1.send_command('ip route add default via 10.0.10.2')
    hs2.send_command('ip route add default via 10.0.30.2')

    ping_result = hs1.send_command('ping -c 1 10.0.30.1')
    platform.destroy()
    assert '1 packets transmitted, 1 received' in ping_result
