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

from topology.platforms.mininet import MininetPlatform, MininetSwitch, \
    MininetHost


class Node(object):
    """mockup Node"""
    def __init__(self, identifier, **kwargs):
        self.metadata = kwargs
        self.identifier = identifier


def test_build_topology():
    """
    Builds (and destroys) a basic topology consisting in one switch and one
    host
    """
    mn = MininetPlatform(None, None)
    mn.pre_build()
    assert mn._net is not None

    s1 = Node('s1')
    mn.add_node(s1)

    assert mn.nmlnode_node_map[s1.identifier] is not None
    assert isinstance(mn.nmlnode_node_map[s1.identifier], MininetSwitch)

    h2 = Node('h2', type='host')
    mn.add_node(h2)

    assert mn.nmlnode_node_map[h2.identifier] is not None
    assert isinstance(mn.nmlnode_node_map[h2.identifier], MininetHost)

    mn.add_bilink((s1, None), (h2, None), None)

    mn.post_build()

    mn.destroy()


def test_send_command():
    """
    Connect two host to a switch and ping h2 from h1

        +------+                  +------+
        |      |     +------+     |      |
        |  h1  <----->  s1  <----->  h2  |
        |      |     +------+     |      |
        +------+                  +------+
    """
    mn = MininetPlatform(None, None)
    mn.pre_build()
    assert mn._net is not None

    s1 = Node('s1')
    mn.add_node(s1)

    h1 = Node('h1', type='host')
    mn_h1 = mn.add_node(h1)

    h2 = Node('h2', type='host')
    mn_h2 = mn.add_node(h2)

    mn.add_bilink((s1, None), (h1, None), None)
    mn.add_bilink((s1, None), (h2, None), None)

    mn.post_build()

    ping_response = mn_h1.send_command('ping -c 1 ' + mn_h2.node.IP())

    mn.destroy()

    assert '1 packets transmitted, 1 received' in ping_response
