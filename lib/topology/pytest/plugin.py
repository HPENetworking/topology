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

This plugin provides a fixture ``topology`` that will load and build a topology
description from the module. This topology must be present in the module as a
constant variable ``TOPOLOGY``. It can be either a string and thus the method
:meth:`topology.manager.TopologyManager.parse` will be used, or a dictionary in
which case the method :meth:`topology.manager.TopologyManager.load` will be
used. Once built, the plugin registers the *unbuild* for when the module has
ended all the tests.

If the ``TOPOLOGY`` variable isn't present the fixture assumes the user will
prefer to build the topology using the standard NML objects with the
:class:`pynml.manager.NMLManager` instance enbeed into the
:class:`topology.manager.TopologyManager`.

To be able to select the engine platform this plugins registers the ``--engine-
platform`` option that can be set in pytest command line.

For reference see:

    http://pytest.org/dev/plugins.html#hook-specification-and-validation
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from traceback import format_exc

from six import PY3
from pytest import fixture, fail

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
    engine = request.config.getoption('--engine-platform')

    # FIXME: Someday mininet... someday... -__-
    if PY3 and engine == 'mininet':
        request.config._warn(
            'Mininet does not support Python3, testing with engine "debug"'
        )
        engine = 'debug'

    module = request.module
    topomgr = TopologyManager(engine)

    # Autobuild topology if available.
    if hasattr(module, 'TOPOLOGY'):

        topo = module.TOPOLOGY

        try:
            if isinstance(topo, dict):
                topomgr.load(topo)
            else:
                topomgr.parse(topo)
            topomgr.build()
        except:
            fail(
                'Error building topogy in module {}:\n{}'.format(
                    module.__name__,
                    format_exc()
                ), pytrace=False
            )

        request.addfinalizer(topomgr.unbuild)

    return topomgr


def pytest_addoption(parser):
    """
    pytest hook to add CLI arguments.
    """
    group = parser.getgroup('general')
    group.addoption(
        '--engine-platform',
        default='mininet',
        help='Select platform to run topology tests',
        choices=sorted(platforms())
    )


__all__ = ['topology', 'pytest_addoption']
