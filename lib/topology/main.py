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
Application entry point module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import sys
import logging
from atexit import register
from os.path import join, basename, splitext

from six import StringIO

from . import __version__
from .manager import TopologyManager
from .interact import interact
from pyszn.parser import find_topology_in_python
from pyszn.injection import parse_attribute_injection
from .logging import manager as logmanager


log = logging.getLogger(__name__)


def main(args):
    """
    Application main function.

    :param args: An arguments namespace.
    :type args: :py:class:`argparse.Namespace`
    :return: Exit code.
    :rtype: int
    """
    print('Starting Network Topology Framework v{}'.format(__version__))

    # Setup framework logging
    logmanager.logging_context = None
    if args.log_dir:
        logmanager.logging_directory = args.log_dir

    # Parse attributes injection file
    injected_attr = None
    if args.inject is not None:
        injection_spec = parse_attribute_injection(args.inject)
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
    module = splitext(basename(args.topology))[0]
    if args.plot_dir:
        plot_file = join(
            args.plot_dir, '{}.{}'.format(module, args.plot_format)
        )
        mgr.nml.save_graphviz(
            plot_file, keep_gv=True
        )

    # Export topology as NML
    if args.nml_dir:
        nml_file = join(
            args.nml_dir, '{}.xml'.format(module)
        )
        mgr.nml.save_nml(
            nml_file, pretty=True
        )

    return 0


__all__ = ['main']
