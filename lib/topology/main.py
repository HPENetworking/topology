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
Application entry point module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging

from . import __version__
from .manager import TopologyManager
from .interact import interact


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

    # Create manager
    mgr = TopologyManager(args.platform)

    # Read topology
    if args.topology.endswith('.py'):
        raise NotImplementedError(
            'Topology extraction from Python files not implemented yet.'
        )
    else:
        with open(args.topology, 'r') as fd:
            mgr.parse(fd.read())

    # Build topology
    print('Building topology, please wait...')
    mgr.build()

    # Start interactive mode if required
    if not args.non_interactive:
        interact(mgr)
        print('Unbuilding topology, please wait...')
        mgr.unbuild()

    return 0


__all__ = ['main']
