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
Topology framework example test.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import pytest  # noqa


TOPOLOGY = """
# Nodes
[shell=vtysh name="Switch 1"] sw1
[shell=vtysh name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
"""


def test_ping(topology):
    sw1 = topology.get('sw1')
    response = sw1.send_command('ping -c 1 10.0.30.1', shell='bash')

    # Do something with ping
    print(response)
