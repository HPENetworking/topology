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

To be able to select the platform engine this plugins registers the
``--topology-platform`` option that can be set in pytest command line.

For reference see:

    http://pytest.org/dev/plugins.html#hook-specification-and-validation
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import getcwd, makedirs
from traceback import format_exc
from collections import OrderedDict
from os.path import join, isabs, abspath, exists, isdir

from pytest import fixture, fail, hookimpl, skip

from topology.logging import get_logger, StepLogger


class TopologyPlugin(object):
    """
    pytest plugin for Topology.

    :param str platform: Platform engine name to run the tests with.
    :param str plot_dir: Directory to auto-plot topologies. ``None`` if
     feature is disabled.
    :param str plot_format: Format to plot the topologies.
    :param str nml_dir: Directory to auto-export topologies. ``None`` if
     feature is disabled.
    """

    def __init__(
            self, platform, plot_dir, plot_format,
            nml_dir, injected_attr, log_dir):
        super(TopologyPlugin, self).__init__()
        self.platform = platform
        self.plot_dir = plot_dir
        self.plot_format = plot_format
        self.nml_dir = nml_dir
        self.injected_attr = injected_attr
        self.log_dir = log_dir

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
        if self.log_dir:
            header.append("          log_dir='{}'".format(
                self.log_dir
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
    from ..manager import TopologyManager
    from ..logging import manager as logmanager

    plugin = request.config._topology_plugin
    module = request.module
    topomgr = TopologyManager(plugin.platform)

    # Setup framework logging
    logmanager.logging_context = module.__name__
    if plugin.log_dir:
        logmanager.logging_directory = plugin.log_dir

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

        # Get topology description
        topo = module.TOPOLOGY

        # Get attributes to inject
        suite_injected_attr = None
        if plugin.injected_attr is not None:
            suite_injected_attr = plugin.injected_attr.get(
                abspath(module.__file__), None
            )

        try:
            if isinstance(topo, dict):
                topomgr.load(topo, inject=suite_injected_attr)
            else:
                topomgr.parse(topo, inject=suite_injected_attr)
            topomgr.build()
        except:
            fail(
                'Error building topology in module {}:\n{}'.format(
                    module.__name__,
                    format_exc()
                ), pytrace=False
            )

        request.addfinalizer(finalizer)

    return topomgr


@fixture(scope='function')
def step(request):
    """
    Fixture to log a step in a test.
    """
    return get_logger(
        OrderedDict([
            ('test_suite', request.module.__name__),
            ('test_case', request.function.__name__)
        ]),
        category='step'
    )


def pytest_addoption(parser):
    """
    pytest hook to add CLI arguments.
    """
    from ..platforms.manager import platforms, DEFAULT_PLATFORM

    group = parser.getgroup('topology', 'Testing of network topologies')
    group.addoption(
        '--topology-platform',
        default=DEFAULT_PLATFORM,
        help='Select platform to run topology tests',
        choices=platforms()
    )
    group.addoption(
        '--topology-plot-dir',
        default=None,
        help='Directory to auto-plot topologies'
    )
    group.addoption(
        '--topology-plot-format',
        default='svg',
        help='Format for plotting topologies'
    )
    group.addoption(
        '--topology-nml-dir',
        default=None,
        help='Directory to export topologies as NML XML'
    )
    group.addoption(
        '--topology-inject',
        default=None,
        help='Path to an attributes injection file'
    )
    group.addoption(
        '--topology-log-dir',
        default=None,
        help='Path to a directory where logs are to be stored'
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
    injection_file = config.getoption('--topology-inject')
    log_dir = config.getoption('--topology-log-dir')

    def create_dir(path):
        if path:
            if not isabs(path):
                path = join(abspath(getcwd()), path)
            if not exists(path):
                makedirs(path)

    # Determine plot, NML and log directory paths and create them if required
    create_dir(plot_dir)
    create_dir(nml_dir)
    create_dir(log_dir)

    # Parse attributes injection file
    from pyszn.injection import parse_attribute_injection
    injected_attr = None
    if injection_file is not None:

        # Get a list of all testing directories
        search_paths = [
            abspath(arg) for arg in config.args if isdir(arg)
        ]

        injected_attr = parse_attribute_injection(
            injection_file,
            search_paths=search_paths
        )

    # Create and register plugin
    config._topology_plugin = TopologyPlugin(
        platform, plot_dir, plot_format.lstrip('.'),
        nml_dir, injected_attr, log_dir
    )
    config.pluginmanager.register(config._topology_plugin)

    # Add test_id marker
    config.addinivalue_line(
        'markers',
        'test_id(id): assign a test identifier to the test'
    )

    # Add topology_compatible marker
    config.addinivalue_line(
        'markers',
        'platform_incompatible(platforms, reason=None): '
        'mark a test as incompatible with a list of platform engines. '
        'Optionally specify a reason for better reporting'
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
    test_id_marker = item.get_marker('test_id')
    incompatible_marker = item.get_marker('platform_incompatible')

    # If marked and xml logging enabled
    if test_id_marker is not None and hasattr(item.config, '_xml'):
        test_id = test_id_marker.args[0]
        item.config._xml.node_reporter(item.nodeid).add_property(
            'test_id', test_id
        )

    if incompatible_marker:
        platform = item.config._topology_plugin.platform
        if platform in incompatible_marker.args[0]:
            message = (
                incompatible_marker.kwargs.get('reason') or (
                    'Test is incompatible with {} platform'.format(platform)
                )
            )
            skip(message)


__all__ = [
    'TopologyPlugin',
    'topology',
    'pytest_addoption',
    'pytest_configure',
    'StepLogger'
]
