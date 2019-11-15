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
Tests for switch.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

TOPOLOGY = """
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2
[type=host name="Host 3"] hs3
[type=switch name="Switch 1"] sw1

[ipv4="192.168.15.1/24" up=True] hs1:1
[ipv4="192.168.15.2/24" up=True] hs2:1
[ipv4="192.168.16.3/24" up=True] hs3:1

hs1:1 -- sw1:p1
hs2:1 -- sw1:p2
hs3:1 -- sw1:p3
"""


def test_ping(topology, step):
    """
    Test that two nodes can ping each other through the switch.
    """
    # Setup which shell to use
    shell = 'bash'

    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    hs3 = topology.get('hs3')

    ping_hs1_to_hs2 = hs1.libs.ping.ping(1, '192.168.15.2', shell=shell)
    ping_hs2_to_hs1 = hs2.libs.ping.ping(1, '192.168.15.1', shell=shell)

    assert ping_hs1_to_hs2['transmitted'] == ping_hs1_to_hs2['received'] == 1
    assert ping_hs2_to_hs1['transmitted'] == ping_hs2_to_hs1['received'] == 1

    # Should not work, host 3 is not in the same subnet as the other 2 hosts
    # We should implement this with ping's communication library once the
    # "network unreachable" scenario is supported by uncommenting the following
    # three lines
    # no_ping = hs3.libs.ping.ping(1, '192.168.15.1', shell=shell)
    # assert no_ping['transmitted'] == 1
    # assert no_ping['received'] == 0
    no_ping = hs3('ping -c 1 192.168.15.1', shell=shell)
    assert 'Network is unreachable' in no_ping

    # Should not work, not node exists with that ip
    no_ping = hs2.libs.ping.ping(1, '192.168.15.3')
    assert no_ping['transmitted'] == 1
    assert no_ping['received'] == 0
