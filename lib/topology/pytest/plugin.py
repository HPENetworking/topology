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

import glob
from json import dumps
from time import time
from pathlib import Path
from logging import getLogger
from typing import Tuple
from deepdiff import DeepHash
from os import getcwd, makedirs
from traceback import format_exc
from collections import OrderedDict
from pyszn.parser import parse_txtmeta
from pytest import fixture, fail, hookimpl, skip
from os.path import join, isabs, abspath, realpath, exists, isdir

from ..manager import TopologyManager
from topology.args import parse_options, ExtendAction
from topology.logging import get_logger, StepLogger


log = getLogger(__name__)


class TopologyPlugin:
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
        self.platform = platform
        self.injected_attr = injected_attr
        self.log_dir = log_dir
        self.szn_dir = szn_dir
        self.platform_options = platform_options
        self.build_retries = build_retries
        self.topomgr: TopologyManager = None
        self.topology_hash: DeepHash = None

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

    def destroy_topology(self):
        """
        Checks if the topology manager instance is built and if so,
        unbuilds it. Then sets the topology manager instance to None and
        resets the topology hash.

        This method should be called when the pytest session ends or when a new
        topology is built, ensuring that the previous topology is properly
        cleaned up before building a new one.
        """
        if self.topomgr is None:
            # No topology manager instance to destroy
            return

        if self.topomgr.is_built():
            log.info(f'Destroying setup with hash {self.topology_hash}')
            self.topomgr.unbuild()

        self.topomgr = None
        self.topology_hash = None


@fixture(scope='module')
def topology(request):
    """
    Fixture that injects a TopologyManager into as a test fixture.

    See:

    - https://pytest.org/latest/fixture.html
    - https://pytest.org/latest/builtin.html#_pytest.python.FixtureRequest
    """
    from ..logging import manager as logmanager

    plugin: TopologyPlugin = request.config._topology_plugin
    module = request.module

    # Setup framework logging
    logmanager.logging_context = module.__name__
    if plugin.log_dir:
        logmanager.logging_directory = plugin.log_dir

    # If --topology-group-by-topology is used, check if the
    # topology_hash is already built and if so, return the existing
    # TopologyManager instance. This allows the topology to be built once
    # per group of tests, rather than rebuilding it for each individual test.
    group_by_topology = request.config.getoption(
        '--topology-group-by-topology'
    )

    if group_by_topology and plugin.topomgr is not None:
        # Fetch topology data for this module
        assert hasattr(module, '__TOPOLOGY_HASH__'), (
            f'Module {module.__name__} has no __TOPOLOGY_HASH__ attribute. '
            'This should have been set when collecting the tests '
            '(there is a bug in topology pytest plugin)'
        )

        module_topology_hash = module.__TOPOLOGY_HASH__

        # If the topology is already built, check if the topology_hash matches
        cached_hash = plugin.topology_hash
        topomgr = plugin.topomgr

        if module_topology_hash == cached_hash:
            # If the topology is already built, return the existing instance
            log.info(
                f'Reusing topology_hash {module_topology_hash} for suite '
                f'{abspath(module.__file__)}'
            )
            return topomgr

    # Either grouping by topology is disabled, or we just finished to run
    # a topology group and this is a new unique topology (or this is the fist
    # topology ever), so we need to build a new topology manager instance for
    # this module. If the topology was already built, destroy it first.
    plugin.destroy_topology()

    topomgr = TopologyManager(
        engine=plugin.platform, options=plugin.platform_options
    )

    plugin.topomgr = topomgr

    module_topology = get_module_topology(plugin, module)

    if module_topology is None:
        fail(
            f'Topology module {module.__name__} is missing TOPOLOGY or '
            'TOPOLOGY_ID variable.',
            pytrace=False
        )

    topology, injected_attr = module_topology

    try:
        if isinstance(topology, dict):
            topomgr.load(topology, inject=injected_attr)
        else:
            topomgr.parse(topology, inject=injected_attr)
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

    if group_by_topology:
        # Notice if grouping by topology is disabled, plugin.topology_hash will
        # always be None, so we will always build a new topology manager
        # instance for each module.
        plugin.topology_hash = module.__TOPOLOGY_HASH__
        plugin.topomgr = topomgr
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
        type=int,
        help='Retry building a topology up to defined times'
    )
    group.addoption(
        '--topology-group-by-topology',
        action='store_true',
        help=(
            'Group tests that share the same TOPOLOGY string, SZN file, and '
            'attribute injection values so they run using a single topology '
            'manager instance. This allows the topology to be built once per '
            'group of tests, rather than rebuilding it for each individual '
            'test. This can significantly reduce test execution time for '
            'large test suites.'
        )
    )
    group.addoption(
        '--topology-topologies-file',
        default=None,
        type=Path,
        help=(
            'File to save the topology information when grouping tests by '
            'topology. If not specified, the topology information will not be '
            'saved.'
        )
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


@hookimpl(trylast=True)
def pytest_unconfigure(config):
    """
    pytest hook to unconfigure plugin.
    """
    plugin: TopologyPlugin = getattr(config, '_topology_plugin', None)
    if plugin:
        plugin.destroy_topology()
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


def get_module_topology(
    plugin: TopologyPlugin,
    module: object
) -> Tuple[dict, dict]:
    """
    Obtain the topology string from the module, either from the
    TOPOLOGY variable or from the SZN file defined by the TOPOLOGY_ID
    variable. If the TOPOLOGY variable is defined, it will be parsed as a
    string or a dictionary, depending on its type. If the TOPOLOGY_ID
    variable is defined, the function will search for a SZN file with the
    same name in the directories specified by the szn_dir option.

    :param plugin: The TopologyPlugin instance containing configuration.
    :param module: The module object to extract the topology from.
    :return: A tuple containing the topology as a dictionary and any
     injected attributes as a dictionary.
    """

    topology_cache = getattr(module, '__TOPOLOGY__', None)
    if topology_cache is not None:
        # If the module already has a cached TOPOLOGY, return it
        log.debug(
            f'Using cache __TOPOLOGY__ for module {module.__name__}'
        )

        # This is a tuple of (topology, injected_attr)
        return topology_cache

    injected_attr = None
    if plugin.injected_attr is not None:
        injected_attr = plugin.injected_attr.get(
            realpath(module.__file__), None
        )

    topology = getattr(module, 'TOPOLOGY', '')
    if topology:   # If topology is defined and not empty
        if isinstance(topology, str):
            topology = parse_txtmeta(topology)
        elif not isinstance(topology, dict):
            fail(
                'Module {} has an invalid TOPOLOGY variable. '
                'It must be a string or a dictionary.'.format(
                    module.__name__
                ),
                pytrace=False
            )

    # If TOPOLOGY is not defined, check for TOPOLOGY_ID
    else:
        topology_id = getattr(module, 'TOPOLOGY_ID', '')

        if not topology_id:
            # No TOPOLOGY or TOPOLOGY_ID was found, this is likely a
            # non-topology test. Let the caller handle it.
            return None

        if not plugin.szn_dir:
            fail(
                'Module {} has TOPOLOGY_ID but no SZN directories defined. '
                'Please set --topology-szn-dir option to a directory '
                'where the SZN files are located.'.format(module.__name__),
                pytrace=False
            )

        for search_path in plugin.szn_dir:
            for filename in glob.glob(
                f'{search_path}/{topology_id}.szn'
            ):
                topology = parse_txtmeta(
                    Path(filename).read_text(encoding='utf-8')
                )

        assert topology, (
            'Module {} has TOPOLOGY_ID but no SZN files found in '
            'the directories: {}'.format(
                module.__name__, ', '.join(plugin.szn_dir)
            )
        )

    # Cache the topology in the module for later use
    module.__TOPOLOGY__ = (topology, injected_attr)
    return topology, injected_attr


def _merge_attributes(
    topology: dict,
    injected_attr: dict
) -> dict:
    """
    Merge the injected attributes into the topology.
    This function updates the topology nodes, ports, and links with the
    injected attributes. It modifies the topology in place.

    :param topology: The topology dictionary to update.
    :param injected_attr: The injected attributes dictionary containing
     nodes, ports, and links to merge into the topology.

    :return: The updated topology dictionary with merged attributes.
    """

    inject_nodes = injected_attr.get('nodes', {})
    inject_ports = injected_attr.get('ports', {})
    inject_links = injected_attr.get('links', {})

    # Merge the topology nodes with the inject nodes
    for topo_node in topology.get('nodes', []):
        for node_id in topo_node.get('nodes', []):
            if node_id in inject_nodes:
                topo_node['attributes'].update(
                    inject_nodes[node_id]
                )

    # Merge the topology ports with the inject ports
    for topo_port in topology.get('ports', []):
        for node_id, port in topo_port.get('ports', []):
            if (node_id, port) in inject_nodes:
                topo_port['attributes'].update(
                    inject_ports[(node_id, port)]
                )

    # Merge the topology links with the inject links
    for topo_link in topology.get('links', []):
        if topo_link['endpoints'] in inject_links:
            topo_link['attributes'].update(
                inject_links[topo_link['endpoints']]
            )
    return topology


def identify_unique_topologies(
    plugin: TopologyPlugin,
    items: list,
) -> OrderedDict:
    """
    Iterate over pytest items and identify unique topologies based on
    the module's TOPOLOGY string or SZN file. Each unique topology is
    identified by a hash of its structure, which is calculated using
    DeepHash from the deepdiff library. In addition, every test module is
    marked with a `__TOPOLOGY_HASH__` attribute.

    This function groups pytest items by their topology, allowing the
    topology to be built once per group of tests, rather than rebuilding it
    for each individual test. This can significantly reduce test execution time
    for large test suites.

    :param plugin: The TopologyPlugin instance containing configuration.
    :param items: List of pytest items to analyze for unique topologies.
    :return: An OrderedDict where keys are topology hashes and values are
     dictionaries containing the topology data and associated items.
    """

    unique_topologies = OrderedDict()

    for item in items:
        # Find if there if this module is already added to a calculated
        # topology and get the topology_hash of that topology, otherwise,
        # this is a new module and we need to calculate the topology_hash
        module = item.module
        module_name = item.module.__name__
        topology_hash = next(
            (
                key for key, value in unique_topologies.items()
                if module_name in value['modules']
            ),
            None
        )

        if topology_hash is None:

            # No topology_hash found for this module. Either this is a new
            # module or this is a non-topology test module.

            # Check if there is a TOPOLOGY or TOPOLOGY_ID variable in the
            # module. If not, this is a non-topology test module.
            module_topology = get_module_topology(plugin, module)

            if module_topology is None:
                # This is a non-topology test module, so group it
                # with other non-topology test modules using topology=None
                topology = None

            else:
                # This a topology test module, so we can
                # calculate the topology_hash for it.
                topology, injected_attr = module_topology

                if injected_attr:
                    # If there are injected attributes, merge them into the
                    # topology
                    topology = _merge_attributes(topology, injected_attr)

            # Create a new topology_hash for this module.
            # Reference:
            #   https://deepdiff.readthedocs.io/en/latest/deephash.html
            topology_hash = DeepHash(topology)[topology]
            module.__TOPOLOGY_HASH__ = topology_hash
            unique_topo = unique_topologies.setdefault(topology_hash, {
                'items': [],
                'modules': {},
                'topology': topology,
                'attributes': ''
            })
            unique_topo['modules'][module_name] = []

        # Add the tests to the topology_hash node
        unique_topologies[topology_hash]['items'].append(item)
        unique_topologies[topology_hash]['modules'][module_name].append(
            item.name
        )

    return unique_topologies


def sort_items_by_topology(
    unique_topologies: OrderedDict,
) -> list:
    """
    Takes a dictionary mapping unique topology hashes to their
    associated test items and returns a flat list of pytest test items
    sorted by their topology hashes.

    :param unique_topologies: OrderedDict of unique topologies with their
     associated test items.
    """

    items = []
    for topology_hash, node in unique_topologies.items():
        functions = ', '.join(
            f'{function.module.__name__}.{function.name}'
            for function in node['items']
        )
        log.debug(
            f'\n\nSetup ID {topology_hash}: {len(node["items"])} \n{functions}'
        )
        items.extend(node.pop('items', []))
    return items


@hookimpl(tryfirst=True)
def pytest_collection_finish(session):
    plugin = session.config._topology_plugin

    unique_topologies = identify_unique_topologies(
        plugin, session.items
    )

    if session.config.getoption("--topology-group-by-topology"):
        # Sort the test items using the topology information on each module
        session.items = sort_items_by_topology(unique_topologies)

    topologies_file = session.config.getoption(
        '--topology-topologies-file'
    )
    if topologies_file is not None:
        # Write the whole json to an output file to be processed later
        topologies_file.write_text(
            dumps(unique_topologies, indent=4),
            encoding='utf-8'
        )


__all__ = [
    'topology',
    'StepLogger',
    'TopologyPlugin',
    'pytest_addoption',
    'pytest_collection_finish',
]
