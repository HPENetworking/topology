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

from time import sleep
from subprocess import check_output

import pytest


TOPOLOGY = """
# +------+                               +------+
# |      |     +------+     +------+     |      |
# |  h1  <----->  s1  <----->  s2  <----->  h2  |
# |      |     +------+     +------+     |      |
# +------+                               +------+

# Nodes
[type=openvswitch name="Switch 1"] sw1
[type=openvswitch name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Ports
[up=True] sw1:1
[up=True] sw1:2
[up=True] sw2:1
[up=True] sw2:2
[ipv4="192.168.0.1/24" up=True] hs1:1
[ipv4="192.168.0.2/24" up=True] hs2:1

# Links
hs1:1 -- sw1:1
sw1:2 -- sw2:2
sw2:1 -- hs2:1
"""


@pytest.mark.skipif(
    'openvswitch' not in check_output('lsmod').decode('utf-8'),
    reason='Requires Open vSwitch kernel module.')
def test_ping_openvswitch(topology):

    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    sw1 = topology.get('sw1')
    sw2 = topology.get('sw2')

    assert hs1 is not None
    assert hs2 is not None
    assert sw1 is not None
    assert sw2 is not None

    # Configure switches
    commands = """
    ovs-vsctl add-br br0
    ovs-vsctl add-port br0 1
    ovs-vsctl add-port br0 2
    ip link set br0 up
    """
    sw1.libs.common.assert_batch(commands)
    sw2.libs.common.assert_batch(commands)

    # Wait for Open vSwitch
    sleep(1)

    # Ping between the hosts
    ping_hs2 = hs1.libs.ping.ping(1, '192.168.0.2')
    assert ping_hs2['transmitted'] == ping_hs2['received'] == 1
