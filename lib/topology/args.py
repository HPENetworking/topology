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
Argument management module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from os.path import isfile, abspath

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

    if not isfile(args.topology):
        log.error('No such file : {}'.format(args.topology))
        exit(1)
    args.topology = abspath(args.topology)

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
        help='Select the platform to build the topology',
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
        'topology',
        help='File with the topology description to build'
    )

    args = parser.parse_args(argv)
    args = validate_args(args)
    return args


__all__ = ['parse_args']
