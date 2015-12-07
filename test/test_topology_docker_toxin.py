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

TOPOLOGY = """
# +------+     +-------+
# |      |     |       |
# | txn1 <----->  hs1  |
# |      |     |       |
# +------+     +-------+

# Nodes
[type=toxin name="Toxin"] txn1
[type=host name="Host"] hs1

# Links
txn1:1 -- hs1:1
"""


def test_toxin(topology):
    """
    Set static routes and test a ping.
    """
    txn1 = topology.get('txn1')
    hs1 = topology.get('hs1')

    assert txn1 is not None
    assert hs1 is not None

    # Setup static routes
    hs1('ifconfig 1 up')

    txn1('ports = [1]')
    txn1('g = GenerationParams()')
    txn1('g.iterations = 250')
    txn1('g.add_packet("DEADBEEFCAFECAFE", 10)')
    txn1('config(ports, g)')
    txn1('start(ports)')

    result = hs1('ifconfig 1')

    assert 'dropped:2500' in result
