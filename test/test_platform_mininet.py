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
Test suite for module topology.

"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import pytest  # noqa

from topology.platforms.mininet import MininetPlatform, MininetSwitch


def test_build_topology():
    mn = MininetPlatform(None, None)
    mn.pre_build()
    assert mn._net is not None

    class Node(object):
        """docstring for  Node"""
        def __init__(self, identifier):
            self.metadata = {}
            self.identifier = identifier

    s1 = Node('s1')
    mn.add_node(s1)

    assert mn.nmlnode_node_map[s1.identifier] is not None
    assert isinstance(mn.nmlnode_node_map[s1.identifier], MininetSwitch)

    s2 = Node('s2')
    mn.add_node(s2)

    assert mn.nmlnode_node_map[s2.identifier] is not None
    assert isinstance(mn.nmlnode_node_map[s2.identifier], MininetSwitch)

    mn.add_bilink((s1, None), (s2, None), None)

    mn.post_build()

    mn.destroy()
