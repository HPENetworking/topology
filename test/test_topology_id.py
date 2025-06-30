# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2025 Hewlett Packard Enterprise Development LP
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
Test suite for TOPOLOGY_ID feature.
"""

TOPOLOGY_ID = 'ring'


def test_topology_id(topology, pytestconfig):
    """
    Verify that when topology_szn_dir is set, the topology is built
    correctly from the SZN files.
    """
    assert pytestconfig.getoption('--topology-szn-dir')
    assert topology.get('sw1') is not None
    assert topology.get('sw2') is not None
    assert topology.get('sw3') is not None
