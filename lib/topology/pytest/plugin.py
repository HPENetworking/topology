# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Hewlett Packard Enterprise Development LP
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
prefer to build the topology using Topology Graph objects directly with the
:class:`topology.graph.TopologyGraph` instance enbeed into the
:class:`topology.manager.TopologyManager`.

To be able to select the platform engine this plugins registers the
``--topology-platform`` option that can be set in pytest command line.

For reference see:

    http://pytest.org/dev/plugins.html#hook-specification-and-validation
"""

from time import time
from logging import getLogger
from os import getcwd, makedirs
from traceback import format_exc
from collections import OrderedDict
from pytest import fixture, fail, hookimpl, skip
from os.path import join, isabs, abspath, realpath, exists, isdir

from topology.args import parse_options, ExtendAction
from topology.logging import get_logger, StepLogger


log = getLogger(__name__)


class TopologyPlugin(object):
    """
    pytest plugin for Topology.

    :param str platform: Platform engine name to run the tests with
    :param dict injected_attr: A dictionary holding topology attributes to
     inject.
    :param str log_dir: Path where to store logs.
    :param list szn_dir: List of paths to directories where ``*.szn`` files
     are located.
    :param dict platform_options: Dictionary holding parameters passed directly
     to the topology platform object.
    :param int build_retries: Amount of times to retry the build stage.
    """

    def __init__(
        self, platform, injected_attr, log_dir, szn_dir, platform_options,
        build_retries
    ):
        super(TopologyPlugin, self).__init__()
        self.platform = platform
        self.injected_attr = injected_attr
        self.log_dir = log_dir
        self.szn_dir = szn_dir
        self.platform_options = platform_options
        self.build_retries = build_retries

    def pytest_report_header(self, config):
        """
        pytest hook to print information of the report header.
        """
        header = ["topology: platform='{}'".format(self.platform)]
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
    topomgr = TopologyManager(
        engine=plugin.platform, options=plugin.platform_options
    )

    # Setup framework logging
    logmanager.logging_context = module.__name__
    if plugin.log_dir:
        logmanager.logging_directory = plugin.log_dir

    # Finalizer unbuild the topology
    def finalizer():

        # Do nothing is topology isn't built
        if not topomgr.is_built():
            return

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
        except Exception:
            fail(
                'Error loading topology in module {}:\n{}'.format(
                    module.__name__,
                    format_exc()
                ),
                pytrace=False
            )

        for iteration in range(plugin.build_retries + 1):
            try:
                topomgr.build()
                log.info(
                    'Attempt {} on building topology was successful'.format(
                        iteration
                    )
                )
                break
            except Exception:
                msg = (
                    '{}\nAttempt {} to build topology failed.'
                ).format(format_exc(), iteration)

                log.warning(msg)
        else:
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
        '--topology-inject',
        default=None,
        help='Path to an attributes injection file'
    )
    group.addoption(
        '--topology-log-dir',
        default=None,
        help='Path to a directory where logs are to be stored'
    )
    group.addoption(
        '--topology-szn-dir',
        default=None,
        action='append',
        help='Path to a directory where szn files are located. '
             'Can be used multiple times'
    )
    group.addoption(
        '--topology-platform-options',
        nargs='+',
        default=None,
        action=ExtendAction,
        help='An argument used by the topology platform '
             'with the form <key>=<value>'
    )
    group.addoption(
        '--topology-build-retries',
        default=0,
        type='int',
        help='Retry building a topology up to defined times'
    )


def pytest_sessionstart(session):
    """
    pytest hook to configure plugin.
    """
    config = session.config
    # Get registered options
    platform = config.getoption('--topology-platform')
    injection_file = config.getoption('--topology-inject')
    log_dir = config.getoption('--topology-log-dir')
    szn_dir = config.getoption('--topology-szn-dir')
    platform_options = config.getoption('--topology-platform-options')
    build_retries = config.getoption('--topology-build-retries')

    if build_retries < 0:
        raise Exception('--topology-build-retries can\'t be less than 0')

    def create_dir(path):
        if path:
            if not isabs(path):
                path = join(abspath(getcwd()), path)
            if not exists(path):
                makedirs(path)

    # Determine log directory paths and create them if required
    create_dir(log_dir)

    # Parse attributes injection file
    from pyszn.injection import parse_attribute_injection
    injected_attr = None
    if injection_file is not None:
        log.info('Processing attribute injection...')
        start_time = time()
        # Get a list of all testing directories
        search_paths = [
            realpath(arg) for arg in config.args if isdir(arg)
        ]

        injected_attr = parse_attribute_injection(
            injection_file,
            search_paths=search_paths,
            ignored_paths=config.getini('norecursedirs'),
            szn_dir=szn_dir
        )
        log.info(
            'Attribute injection completed after {}s'
            .format(time() - start_time)
        )

    # Create and register plugin
    config._topology_plugin = TopologyPlugin(
        platform,
        injected_attr,
        log_dir,
        szn_dir,
        parse_options(platform_options),
        build_retries
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
    test_id_marker = item.get_closest_marker('test_id')
    incompatible_marker = item.get_closest_marker('platform_incompatible')

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
    'StepLogger'
]
