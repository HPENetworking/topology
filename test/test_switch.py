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
Test for basic switching behaviour
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division


TOPOLOGY = """
# +-------+                                 +-------+
# |       |     +-------+     +-------+     |       |
# |  hs1  <----->  sw1  <----->  sw2  <----->  hs2  |
# |       |     +-------+     +-------+     |       |
# +-------+                                 +-------+

# Nodes
[type=p4switch name="Switch 1"] sw1
[type=p4switch name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- sw1:3
sw1:4 -- sw2:3
sw2:4 -- hs2:1
"""


def test_ping(topology):

    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    sw1 = topology.get('sw1')
    sw2 = topology.get('sw2')

    assert hs1 is not None
    assert hs2 is not None
    assert sw1 is not None
    assert sw2 is not None

    hs1('ip link set dev 1 up')
    hs1('ip addr add 10.0.30.1/24 dev 1')
    hs2('ip link set dev 1 up')

    # Test ping
    ping_result = hs2('ping -c 1 10.0.30.1')
    print(ping_result)
    assert '1 packets transmitted, 1 received' in ping_result
