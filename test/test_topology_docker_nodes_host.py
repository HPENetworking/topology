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
Tests for hosts.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division


TOPOLOGY = """
[image="ubuntu:12.04" type=host name="Host 1"] hs1
[type=host name="Host 1"] hs2

[ipv4="192.168.15.1/24" up=True] hs1:1
[ipv4="192.168.15.2/24" up=True] hs2:1

hs1:1 -- hs2:1
"""


def test_image(topology, step):
    """
    Test that image selection features works as expected.
    """
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    issue = hs1('cat /etc/issue', shell='bash')
    assert '12.04' in issue

    issue = hs2('cat /etc/issue', shell='bash')
    assert '14.04' in issue


def test_ping(topology, step):
    """
    Test that two nodes can ping themselves.
    """
    hs1 = topology.get('hs1')  # noqa
    hs2 = topology.get('hs2')

    # FIXME: Ubuntu 12.04 doesn't have ping pre-installed
    # ping_hs1_to_hs2 = hs1.libs.ping.ping(1, '192.168.15.2')
    # assert ping_hs1_to_hs2['transmitted'] == ping_hs1_to_hs2['received'] == 1

    ping_hs2_to_hs1 = hs2.libs.ping.ping(1, '192.168.15.1')
    assert ping_hs2_to_hs1['transmitted'] == ping_hs2_to_hs1['received'] == 1

    # Should not work, not node exists with that ip
    no_ping = hs2.libs.ping.ping(1, '192.168.15.3')
    assert no_ping['transmitted'] == 1
    assert no_ping['received'] == 0
