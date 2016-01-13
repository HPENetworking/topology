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
Test suite for module topology.pytest.plugin.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from pytest import config, mark

# Reload module to properly measure coverage
from six.moves import reload_module

import topology.pytest.plugin
from topology.manager import TopologyManager

reload_module(topology.pytest.plugin)

TOPOLOGY = """
# Nodes
[shell=vtysh name="Switch 1"] sw1
[shell=vtysh name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
[attr1=1] sw1:2 -- sw2:2
"""


@mark.test_id(1000)
def test_build(topology):
    """
    Test automatic build and unbuild of the topology using pytest plugin.
    """
    assert config.pluginmanager.getplugin('topology')
    assert isinstance(topology, TopologyManager)
    assert topology.get('sw1') is not None
    assert topology.get('sw2') is not None
    assert topology.get('hs1') is not None
    assert topology.get('hs2') is not None


@mark.test_id(1001)
@mark.skipif(True, reason='This test must always skip')
def test_skipped_test_id():
    """
    This test must be skipped always, it allows to test if a test_id is always
    recorded even when the test is skipped.
    """
    assert False


@mark.skipif(not hasattr(config, '_xml'), reason='XML output not enabled')
def test_previous_has_test_id():
    """
    Test that previous test recorded the test_id.
    """
    assert hasattr(config, '_xml')
    xml = str(config._xml.tests[-1])
    assert '<property name="test_id" value="1001"/>' in xml


@mark.platform_incompatible(['debug'])
def test_incompatible_marker():
    """
    Test that the incompatible marker is interpreted.
    """
    assert False
