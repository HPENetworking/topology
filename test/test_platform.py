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
Test suite for module topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import getuid


from pytest import mark
from pynml import Node, BidirectionalPort

from topology_docker.platform import DockerPlatform


@mark.skipif(getuid() != 0, reason="Requires root permissions")
def test_add_port():
    """

    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    hs1 = Node(identifier='hs1', type='host')
    topo.add_node(hs1)
    assert topo.nmlnode_node_map[hs1.identifier] is not None

    # Add ports
    p1 = BidirectionalPort(identifier='p1')
    topo.add_biport(hs1, p1)
    p2 = BidirectionalPort(identifier='p2')
    topo.add_biport(hs1, p2)
    p3 = BidirectionalPort(identifier='p3')
    topo.add_biport(hs1, p3)

    # Add link
    topo.add_bilink((hs1, p1), (hs1, p2), None)

    topo.post_build()

    # FIXME: change this for the node send_command
    from subprocess import Popen, PIPE
    from shlex import split as shplit

    result, err = Popen(
        shplit('docker exec hs1 ip link list'),
        stdout=PIPE, stderr=PIPE).communicate()

    topo.destroy()

    assert 'p1' in str(result)
    assert 'p2' in str(result)
    assert 'p3' in str(result)


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


def test_vtysh():
    """
    Checks that the vtysh shell of a host sends a proper reply.
    """
    topo = DockerPlatform(None, None)
    topo.pre_build()

    nml_host = Node(identifier='nml_host2', type='switch', image='testimage')
    host = topo.add_node(nml_host)

    topo.post_build()

    reply = host.send_command('show vlan', shell='vtysh')

    topo.destroy()

    assert 'vlan' in str(reply)


@mark.skipif(getuid() != 0, reason="Requires root permissions")
def test_build_topology():
    """
    Builds (and destroys) a basic topology consisting in one switch and one
    host
    """
    mn = DockerPlatform(None, None)
    mn.pre_build()

    hs1 = Node(identifier='hs1', type='host')
    mn.add_node(hs1)

    assert mn.nmlnode_node_map[hs1.identifier] is not None

    s1 = Node(identifier='s1', type='host')
    mn.add_node(s1)
    p1 = BidirectionalPort(identifier='p1')

    p2 = BidirectionalPort(identifier='p2')

    mn.add_bilink((hs1, p1), (s1, p2), None)

    assert mn.nmlnode_node_map[hs1.identifier] is not None

    mn.post_build()

    # FIXME: change this for the node send_command
    from subprocess import check_call, Popen, PIPE
    from shlex import split as shplit

    check_call(
        shplit(
            'docker exec hs1 ifconfig p1 10.1.1.1 netmask 255.255.255.0 up'))

    check_call(
        shplit('docker exec s1 ifconfig p2 10.1.1.2 netmask 255.255.255.0 up'))

    ping_result, err = Popen(
        shplit('docker exec s1 ping -c 1 10.1.1.1'),
        stdout=PIPE, stderr=PIPE).communicate()

    mn.destroy()

    assert '1 packets transmitted, 1 received' in str(ping_result)


@mark.skipif(getuid() != 0, reason='Mininet requires root permissions')
def test_ping():
    """
    Connect two host to a switch and ping h2 from h1

    ::

        +------+                               +------+
        |      |     +------+     +------+     |      |
        |  h1  <----->  s1  <----->  s2  <----->  h2  |
        |      |     +------+     +------+     |      |
        +------+                               +------+
    """
    mn = DockerPlatform(None, None)
    mn.pre_build()

    s1 = Node(identifier='s1', image='testimage')
    mn.add_node(s1)

    s2 = Node(identifier='s2', image='testimage')
    mn.add_node(s2)

    h1 = Node(identifier='h1', type='host')
    mn.add_node(h1)

    h2 = Node(identifier='h2', type='host')
    mn.add_node(h2)

    s1p1 = BidirectionalPort(identifier='s1p1')
    s1p2 = BidirectionalPort(identifier='s1p2')

    s2p1 = BidirectionalPort(identifier='s2p1')
    s2p2 = BidirectionalPort(identifier='s2p2')

    h1p1 = BidirectionalPort(identifier='h1p1')
    h2p1 = BidirectionalPort(identifier='h2p1')

    mn.add_bilink((s1, s1p1), (h1, h1p1), None)
    mn.add_bilink((s1, s1p2), (s2, s2p1), None)
    mn.add_bilink((s2, s2p2), (h2, h2p1), None)

    mn.post_build()

    # FIXME: change this for the node send_command
    from subprocess import check_call, Popen, PIPE
    from shlex import split as shplit

    check_call(
        shplit(
            'docker exec h1 ifconfig h1p1 10.0.10.1 netmask 255.255.255.0 up'))
    check_call(
        shplit(
            'docker exec h2 ifconfig h2p1 10.0.30.1 netmask 255.255.255.0 up'))

    check_call(
        shplit(
            'docker exec s1 ifconfig s1p1 10.0.10.2 netmask 255.255.255.0 up'))
    check_call(
        shplit(
            'docker exec s1 ifconfig s1p2 10.0.20.1 netmask 255.255.255.0 up'))

    check_call(
        shplit(
            'docker exec s2 ifconfig s2p1 10.0.20.2 netmask 255.255.255.0 up'))
    check_call(
        shplit(
            'docker exec s2 ifconfig s2p2 10.0.30.2 netmask 255.255.255.0 up'))

    check_call(
        shplit(
            'docker exec s1 route add -net 10.0.30.0 netmask \
            255.255.255.0 gw 10.0.20.2'))
    check_call(
        shplit(
            'docker exec s2 route add -net 10.0.10.0 netmask \
            255.255.255.0 gw 10.0.20.1'))

    check_call(
        shplit(
            'docker exec h1 route add default gw 10.0.10.2'))
    check_call(
        shplit(
            'docker exec h2 route add default gw 10.0.30.2'))

    ping_result, err = Popen(
        shplit('docker exec h1 ping -c 1 10.0.30.1'),
        stdout=PIPE, stderr=PIPE).communicate()

    mn.destroy()

    assert '1 packets transmitted, 1 received' in str(ping_result)
