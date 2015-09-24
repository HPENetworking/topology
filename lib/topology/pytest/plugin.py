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

To be able to select the engine platform this plugins registers the
``--topology-platform`` option that can be set in pytest command line.

For reference see:

    http://pytest.org/dev/plugins.html#hook-specification-and-validation
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from os import getcwd, makedirs
from traceback import format_exc
from os.path import join, isabs, abspath, exists

from pytest import fixture, fail, hookimpl

from ..manager import TopologyManager
from ..platforms.manager import platforms, DEFAULT_PLATFORM


log = logging.getLogger(__name__)


class TopologyPlugin(object):
    """
    pytest plugin for Topology.

    :param str platform: Engine platform name to run the tests with.
    :param plot_dir platform: Directory to auto-plot topologies. ``None`` if
     feature is disabled.
    :param plot_format platform: Format to plot the topologies.
    """

    def __init__(self, platform, plot_dir, plot_format, nml_dir):
        self.platform = platform
        self.plot_dir = plot_dir
        self.plot_format = plot_format
        self.nml_dir = nml_dir

    def pytest_report_header(self, config):
        """
        pytest hook to print information of the report header.
        """
        header = ["topology: platform='{}'".format(self.platform)]
        if self.plot_dir:
            header.append("          plot_dir='{}' ({})".format(
                self.plot_dir, self.plot_format
            ))
        if self.nml_dir:
            header.append("          nml_dir='{}'".format(
                self.nml_dir
            ))

        return '\n'.join(header)


@fixture(scope='module')
def topology(request):
    """
    Fixture that injects a TopologyManager into as a test fixture.

    See:

    - https://pytest.org/latest/fixture.html
    - https://pytest.org/latest/builtin.html#_pytest.python.FixtureRequest
    """
    plugin = request.config._topology_plugin
    module = request.module
    topomgr = TopologyManager(plugin.platform)

    # Finalizer unbuild the topology and plot it
    def finalizer():

        # Do nothing is topology isn't built
        if not topomgr.is_built():
            return

        # Plot topology
        if plugin.plot_dir:
            plot_file = join(
                plugin.plot_dir,
                '{}.{}'.format(module.__name__, plugin.plot_format)
            )
            topomgr.nml.save_graphviz(
                plot_file, keep_gv=True
            )

        # Export topology as NML
        if plugin.nml_dir:
            nml_file = join(
                plugin.nml_dir,
                '{}.xml'.format(module.__name__)
            )
            topomgr.nml.save_nml(
                nml_file, pretty=True
            )

        topomgr.unbuild()

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

        request.addfinalizer(finalizer)

    return topomgr


def pytest_addoption(parser):
    """
    pytest hook to add CLI arguments.
    """
    group = parser.getgroup('topology', 'Testing of network topologies')
    group.addoption(
        '--topology-platform',
        default=DEFAULT_PLATFORM,
        help='Select platform to run topology tests',
        choices=sorted(platforms())
    )
    group.addoption(
        '--topology-plot-dir',
        default=None,
        help='Directory to auto-plot topologies'
    )
    group.addoption(
        '--topology-plot-format',
        default='svg',
        help='Format for ploting topologies'
    )
    group.addoption(
        '--topology-nml-dir',
        default=None,
        help='Directory to export topologies as NML XML'
    )


def pytest_configure(config):
    """
    pytest hook to configure plugin.
    """
    # Get registered options
    platform = config.getoption('--topology-platform')
    plot_format = config.getoption('--topology-plot-format')
    plot_dir = config.getoption('--topology-plot-dir')
    nml_dir = config.getoption('--topology-nml-dir')

    # Determine plot directory and create it if required
    if plot_dir:
        if not isabs(plot_dir):
            plot_dir = join(abspath(getcwd()), plot_dir)
        if not exists(plot_dir):
            makedirs(plot_dir)

    # Determine NML export directory and create it if required
    if nml_dir:
        if not isabs(nml_dir):
            nml_dir = join(abspath(getcwd()), nml_dir)
        if not exists(nml_dir):
            makedirs(nml_dir)

    # Create and register plugin
    config._topology_plugin = TopologyPlugin(
        platform, plot_dir, plot_format.lstrip('.'), nml_dir
    )
    config.pluginmanager.register(config._topology_plugin)

    # Add test_id marker
    config.addinivalue_line(
        'markers',
        'test_id(id): assign a test identifier to the test'
    )


def pytest_unconfigure(config):
    """
    pytest hook to unconfigure plugin.
    """
    plugin = getattr(config, '_topology_plugin', None)
    if plugin:
        del config._topology_plugin
        config.pluginmanager.unregister(plugin)


@hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    pytest hook to setup test before run.
    """
    marker = item.get_marker('test_id')

    # If not marked do nothing
    if marker is None:
        return

    # If xml output is not enabled do nothing
    if not hasattr(item.config, '_xml'):
        return

    test_id = marker.args[0]
    item.config._xml.add_custom_property('test_id', test_id)


__all__ = [
    'TopologyPlugin',
    'topology',
    'pytest_addoption',
    'pytest_configure'
]
