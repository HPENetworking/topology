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
Tests for hosts
"""

TOPOLOGY = """
[image="ubuntu:12.04" type=host name="Host 1"] hs1
[type=host name="Host 1"] hs2

hs1:1 -- hs2:1
"""

from docker import Client
from pytest import mark

clnt = Client()

u_1204 = [img for img in clnt.images() if 'ubuntu:12.04' in img['RepoTags']]
u_1404 = [img for img in clnt.images() if 'ubuntu:latest' in img['RepoTags']]


@mark.skipif(
    not u_1204 or not u_1404,
    reason='Ubuntu images for 12.04 and 14.04 are required for this test.'
)
def test_image(topology, step):
    """
    Test that a vlan configuration is functional with a OpenSwitch switch.
    """
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    assert '12.04' in (hs1('cat /etc/issue', shell='bash'))
    assert '14.04' in (hs2('cat /etc/issue', shell='bash'))
