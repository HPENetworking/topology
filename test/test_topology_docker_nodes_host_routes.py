# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Hewlett Packard Enterprise Development LP
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
OpenSwitch Test for simple static routes between nodes.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division


TOPOLOGY = """
# +-------+     +-------+     +-------+     +-------+
# |       |     |       |     |       |     |       |
# |  hs1  <----->  hs2  <----->  hs3  <----->  hs4  |
# |       |     |       |     |       |     |       |
# +-------+     +-------+     +-------+     +-------+

# Nodes
[type=host] hs1 hs2 hs3 hs4

# Ports
[ipv4="10.0.10.1/24" up=True] hs1:right
[ipv4="10.0.10.2/24" up=True] hs2:left
[ipv4="10.0.20.1/24" up=True] hs2:right
[ipv4="10.0.20.2/24" up=True] hs3:left
[ipv4="10.0.30.1/24" up=True] hs3:right
[ipv4="10.0.30.2/24" up=True] hs4:left

# Links
hs1:right -- hs2:left
hs2:right -- hs3:left
hs3:right -- hs4:left
"""


def test_route(topology):
    """
    Set static routes and test a ping.
    """
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    hs3 = topology.get('hs3')
    hs4 = topology.get('hs4')

    assert hs1 is not None
    assert hs2 is not None
    assert hs3 is not None
    assert hs4 is not None

    # Setup static routes
    hs1.libs.ip.add_route('default', '10.0.10.2')
    hs2.libs.ip.add_route('10.0.30.0/24', '10.0.20.2')
    hs3.libs.ip.add_route('10.0.10.0/24', '10.0.20.1')
    hs4.libs.ip.add_route('default', '10.0.30.1')

    # Test ping
    ping = hs1.libs.ping.ping(5, '10.0.30.2')
    assert ping['transmitted'] == ping['received'] == 5
