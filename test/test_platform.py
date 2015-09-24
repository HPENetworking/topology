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

from os import getuid


from pytest import mark
from pynml import Node

from topology_docker.platform import DockerPlatform


@mark.skipif(getuid() != 0, reason="Requires root permissions")
def test_build_topology():
    """
    Builds (and destroys) a basic topology consisting in one switch and one
    host
    """
    mn = DockerPlatform(None, None)
    mn.pre_build()

    hs1 = Node(identifier='hs1', type='host')
    mn.add_node(hs1)

    assert mn.nmlnode_node_map[hs1.identifier] is not None

    s1 = Node(identifier='s1', type='host')
    mn.add_node(s1)

    p1 = Node(identifier='p1')
    p2 = Node(identifier='p2')

    mn.add_bilink((hs1, p1), (s1, p2), None)

    assert mn.nmlnode_node_map[hs1.identifier] is not None

    mn.post_build()

    # mn.destroy()
