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
topology pytest plugin module entry point.

This plugin gets the topology description from the test suite
and handles it to be created. It also gets the topology platform
specifier and sends it to let the topology creator know which platform
to use.

This plugin defines that the topology is to be destroyed once
the last test using this fixture has ended its execution.

This plugin provides the --platform option, so it can be set when
the user runs a test suite.

For reference see:

    https://pytest.org/latest/plugins.html#well-specified-hooks
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging

from pytest import fixture

from ..manager import TopologyManager
from ..platforms.manager import platforms


log = logging.getLogger(__name__)


@fixture(scope='module')
def topology(request):
    """
    Fixture that injects a TopologyManager into as a test fixture.

    See:

    - https://pytest.org/latest/fixture.html
    - https://pytest.org/latest/builtin.html#_pytest.python.FixtureRequest
    """
    topomgr = TopologyManager(request.config.topology)
    request.addfinalizer(topomgr.unbuild)

    # Autobuild topology if available
    # FIXME: Skip all module if parsing or build fails
    if hasattr(request.module, 'TOPOLOGY'):
        topomgr.parse(request.module.TOPOLOGY)
        topomgr.build()

    return topomgr


def pytest_addoption(parser):
    """
    pytest hook to add CLI arguments.
    """
    group = parser.getgroup('general')
    group.addoption(
        '--platform',
        default='mininet',
        help='Select platform to run topology tests',
        choices=sorted(platforms())
    )


__all__ = ['topology', 'pytest_addoption']
