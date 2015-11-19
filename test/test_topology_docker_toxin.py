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
# +-------+     +-------+
# |       |     |       |
# |  hs1  <----->  hs2  |
# |       |     |       |
# +-------+     +-------+

# Nodes
[type=toxin name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- hs2:1

"""


def test_toxin(topology):
    """
    Set static routes and test a ping.
    """
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    assert hs1 is not None
    assert hs2 is not None

    # Setup static routes
    hs2('ifconfig 1 up')

    hs1('ports = [1]', shell='txn-shell')
    hs1('g = GenerationParams()', shell='txn-shell')
    hs1('g.iterations = 250', shell='txn-shell')
    hs1('g.add_packet("DEADBEEFCAFECAFE", 10)', shell='txn-shell')
    hs1('config(ports, g)', shell='txn-shell')
    hs1('start(ports)', shell='txn-shell')

    result = hs2('ifconfig 1')

    assert 'dropped:2500' in result
