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
topology executable module entry point.
"""

import sys
import logging
from io import StringIO
from pathlib import Path
from warnings import warn
from atexit import register

from pyszn.parser import find_topology_in_python
from pyszn.injection import parse_attribute_injection

from . import __version__
from .interact import interact
from .manager import TopologyManager
from .logging import manager as logmanager
from .args import parse_args, InvalidArgument


log = logging.getLogger(__name__)


def main(args):
    """
    Application main function.

    :param args: An arguments namespace.
    :type args: :py:class:`argparse.Namespace`

    :return: Exit code.
    :rtype: int
    """
    print('Starting Topology Framework v{}'.format(__version__))

    # Setup framework logging
    logmanager.logging_context = None
    if args.log_dir:
        logmanager.logging_directory = args.log_dir

    # Parse attributes injection file
    injected_attr = None
    if args.inject is not None:
        injection_spec = parse_attribute_injection(
            args.inject,
            search_paths=[
                Path(args.topology).parent,
            ]
        )
        injected_attr = injection_spec.get(args.topology, None)

    # Create manager
    mgr = TopologyManager(args.platform)

    # Read topology
    if args.topology.endswith('.py'):

        topology = find_topology_in_python(args.topology)

        if topology is None:
            log.error(
                'TOPOLOGY variable could not be found in file {}'.format(
                    args.topology
                )
            )
            return 1

        mgr.parse(topology, inject=injected_attr)
    else:
        with open(args.topology, 'r') as fd:
            mgr.parse(fd.read(), inject=injected_attr)

    print('Building topology, please wait...')

    # Capture stdout to hide commands during build
    if not args.show_build_commands:
        sys.stdout = StringIO()

    # Build topology
    mgr.build()

    # Restore stdout after build
    if not args.show_build_commands:
        sys.stdout = sys.__stdout__

    # Start interactive mode if required
    if not args.non_interactive:

        # Register unbuild
        def unbuild():
            print('Unbuilding topology, please wait...')
            mgr.unbuild()
        register(unbuild)

        interact(mgr)

    # Plot and export topology
    if args.plot_dir:
        warn('--plot-dir is no longer supported, ignoring', DeprecationWarning)

    # Export topology as NML
    if args.nml_dir:
        warn('--nml-dir is no longer supported, ignoring', DeprecationWarning)

    return 0


def __main__():  # noqa: N807
    # Parse arguments
    try:
        args = parse_args()
    except InvalidArgument as e:
        log.critical(e)
        exit(1)

    # Run program
    exit(main(args))


if __name__ == '__main__':
    __main__()


__all__ = [
    'main',
]
