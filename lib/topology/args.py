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
Argument management module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from os import getcwd, makedirs
from os.path import join, isabs, abspath, exists, isfile

from . import __version__
from .platforms.manager import platforms, DEFAULT_PLATFORM


log = logging.getLogger(__name__)


FORMAT = '%(asctime)s:::%(levelname)s:::%(message)s'
V_LEVELS = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


def validate_args(args):
    """
    Validate that arguments are valid.

    :param args: An arguments namespace.
    :type args: :py:class:`argparse.Namespace`
    :return: The validated namespace.
    :rtype: :py:class:`argparse.Namespace`
    """
    level = V_LEVELS.get(args.verbose, logging.DEBUG)
    logging.basicConfig(format=FORMAT, level=level)

    log.debug('Raw arguments:\n{}'.format(args))

    # Verify topology file exists
    if not isfile(args.topology):
        log.error('No such file : {}'.format(args.topology))
        exit(1)
    args.topology = abspath(args.topology)

    # Determine plot directory and create it if required
    if args.plot_dir:
        if not isabs(args.plot_dir):
            args.plot_dir = join(abspath(getcwd()), args.plot_dir)
        if not exists(args.plot_dir):
            makedirs(args.plot_dir)

    # Determine NML export directory and create it if required
    if args.nml_dir:
        if not isabs(args.nml_dir):
            args.nml_dir = join(abspath(getcwd()), args.nml_dir)
        if not exists(args.nml_dir):
            makedirs(args.nml_dir)

    # Verify inject file exists
    if args.inject:
        if not isfile(args.inject):
            log.error('No such file : {}'.format(args.inject))
            exit(1)
        args.inject = abspath(args.inject)

    return args


def parse_args(argv=None):
    """
    Argument parsing routine.

    :param argv: A list of argument strings.
    :rtype argv: list
    :return: A parsed and verified arguments namespace.
    :rtype: :py:class:`argparse.Namespace`
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            'Network Topology Framework using NML, '
            'with support for pytest.'
        )
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Increase verbosity level',
        default=0,
        action='count'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Network Topology Framework v{}'.format(__version__)
    )

    parser.add_argument(
        '--platform',
        default=DEFAULT_PLATFORM,
        help='Platform engine to build the topology with',
        choices=platforms()
    )
    parser.add_argument(
        '--non-interactive',
        help='Just build the topology and exit',
        action='store_true'
    )
    parser.add_argument(
        '--show-build-commands',
        help='Show commands executed in nodes during build',
        action='store_true'
    )
    parser.add_argument(
        '--plot-dir',
        default=None,
        help='Directory to auto-plot topologies'
    )
    parser.add_argument(
        '--plot-format',
        default='svg',
        help='Format for plotting topologies'
    )
    parser.add_argument(
        '--nml-dir',
        default=None,
        help='Directory to export topologies as NML XML'
    )
    parser.add_argument(
        '--inject',
        default=None,
        help='Path to an attributes injection file'
    )

    parser.add_argument(
        'topology',
        help='File with the topology description to build'
    )

    args = parser.parse_args(argv)
    args = validate_args(args)
    return args


__all__ = ['parse_args']
