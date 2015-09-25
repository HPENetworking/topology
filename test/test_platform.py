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
Test suite for module docker platform.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import getuid, environ


from pytest import mark
from pynml import Node, BidirectionalPort

from topology_docker.platform import DockerPlatform


OPS_IMAGE = environ.get('OPS_IMAGE', 'ops:latest')


@mark.skipif(getuid() != 0, reason='Requires root permissions')
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

    assert '2: <BROADCAST,MULTICAST> ' in str(result)
    assert 'p2' in str(result)
    assert 'p3' in str(result)


@mark.skipif(getuid() != 0, reason='Requires root permissions')
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

    assert 'var' in str(reply)


@mark.skipif(getuid() != 0, reason='Requires root permissions')
def test_vtysh():
    """
    Checks that the vtysh shell of a host sends a proper reply.
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    nml_host = Node(
        identifier='nml_host2', type='switch', image=OPS_IMAGE
    )
    host = topo.add_node(nml_host)

    topo.post_build()

    reply = host.send_command('show vlan', shell='vtysh')

    topo.destroy()

    assert 'vlan' in str(reply)


@mark.skipif(getuid() != 0, reason='Requires root permissions')
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

    p2 = BidirectionalPort(identifier='p2')

    topo.add_bilink((hs1, p1), (s1, p2), None)

    assert topo.nmlnode_node_map[hs1.identifier] is not None

    topo.post_build()

    topo_hs1.send_command('ifconfig p1 10.1.1.1 netmask 255.255.255.0 up')

    topo_hs2.send_command('ifconfig p2 10.1.1.2 netmask 255.255.255.0 up')

    ping_result = topo_hs2.send_command('ping -c 1 10.1.1.1')

    topo.destroy()

    assert '1 packets transmitted, 1 received' in str(ping_result)


@mark.skipif(getuid() != 0, reason='Requires root permissions')
def test_ping():
    """
    Builds the topology described on the following schema and ping h2 from h1

    ::

        +------+                               +------+
        |      |     +------+     +------+     |      |
        |  h1  <----->  s1  <----->  s2  <----->  h2  |
        |      |     +------+     +------+     |      |
        +------+                               +------+
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    s1 = Node(identifier='s1', image=OPS_IMAGE)
    topo_s1 = topo.add_node(s1)

    s2 = Node(identifier='s2', image=OPS_IMAGE)

    topo_s2 = topo.add_node(s2)

    h1 = Node(identifier='h1', type='host')
    topo_h1 = topo.add_node(h1)

    h2 = Node(identifier='h2', type='host')
    topo_h2 = topo.add_node(h2)

    s1p1 = BidirectionalPort(identifier='s1p1')
    s1p2 = BidirectionalPort(identifier='s1p2')

    s2p1 = BidirectionalPort(identifier='s2p1')
    s2p2 = BidirectionalPort(identifier='s2p2')

    h1p1 = BidirectionalPort(identifier='h1p1')
    h2p1 = BidirectionalPort(identifier='h2p1')

    topo.add_bilink((s1, s1p1), (h1, h1p1), None)
    topo.add_bilink((s1, s1p2), (s2, s2p1), None)
    topo.add_bilink((s2, s2p2), (h2, h2p1), None)

    topo.post_build()

    topo_h1.send_command('ifconfig h1p1 up')
    topo_h1.send_command('ifconfig h2p1 up')

    topo_h1.send_command('ifconfig h1p1 10.0.10.1 netmask 255.255.255.0 up')
    topo_h2.send_command('ifconfig h2p1 10.0.30.1 netmask 255.255.255.0 up')

    topo_s1.send_command('ip netns exec swns ifconfig s1p1 up', shell='bash')
    topo_s1.send_command('ip netns exec swns ifconfig s1p2 up', shell='bash')

    topo_s1.send_command(
        'ip netns exec swns ifconfig s1p1 10.0.10.2 netmask 255.255.255.0 up',
        shell='bash'
    )
    topo_s1.send_command(
        'ip netns exec swns ifconfig s1p2 10.0.20.1 netmask 255.255.255.0 up',
        shell='bash'
    )

    topo_s2.send_command('ip netns exec swns ifconfig s2p1 up', shell='bash')
    topo_s2.send_command('ip netns exec swns ifconfig s2p2 up', shell='bash')

    topo_s2.send_command(
        'ip netns exec swns ifconfig s2p1 10.0.20.2 netmask 255.255.255.0 up',
        shell='bash'
    )
    topo_s2.send_command(
        'ip netns exec swns ifconfig s2p2 10.0.30.2 netmask 255.255.255.0 up',
        shell='bash'
    )

    topo_s1.send_command(
        'ip netns exec swns route add -net 10.0.30.0 netmask 255.255.255.0 \
        gw 10.0.20.2',
        shell='bash'
    )
    topo_s2.send_command(
        'ip netns exec swns route add -net 10.0.10.0 netmask 255.255.255.0 \
         gw 10.0.20.1',
        shell='bash'
    )

    topo_h1.send_command('route add default gw 10.0.10.2')
    topo_h2.send_command('route add default gw 10.0.30.2')

    ping_result = topo_h1.send_command('ping -c 1 10.0.30.1')

    topo.destroy()

    assert '1 packets transmitted, 1 received' in str(ping_result)
