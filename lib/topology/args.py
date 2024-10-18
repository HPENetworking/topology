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
Argument management module.
"""

import logging
from re import compile
from pprint import pformat
from os import getcwd, makedirs
from collections import OrderedDict
from argparse import Action, ArgumentParser
from os.path import join, isabs, abspath, isfile

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
REGEX_SLUG = compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')


class ExtendAction(Action):
    """
    Action that allows to combine nargs='+' with the action='append' behavior
    but generating a flat list.

    This allow to specify in a argument parser class an option that allows
    to specify multiple values per argument and multiple arguments.

    Usage::

        parser = ArgumentParser(...)
        parser.register('action', 'extend', ExtendAction)

        parser.add_argument(
            '-o', '--option',
            nargs='+',
            dest='options',
            action='extend',
            help='Some description'
        )

    Then, in CLI::

        executable --option var1=var1 var2=var2 --option var3=var3

    And this generates a::

        Namespace(options=['var1=var1', 'var2=var2', 'var3=var3'])
    """

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


class InvalidArgument(Exception):
    """
    Typed exception that allows to fail in argument parsing and verification
    without quiting the process.
    """
    pass


def booleanize(value):
    """
    Convert a string to a boolean.

    :raises: ValueError if unable to convert.

    :param str value: String to convert.

    :return: True for 'yes' and 'true', False for 'no' and
     'false'. Not case sensitive.
    :rtype: bool
    """
    valuemap = {
        'true': True,
        'yes': True,
        'false': False,
        'no': False,
    }
    casted = valuemap.get(value.lower(), None)
    if casted is None:
        raise ValueError(str(value))
    return casted


def parse_options(raw):
    """
    Parse a list of options given by the user.

    :param list raw: Raw options given by the user in the CLI. Raw options are
     in the form:

     .. code-block:: python3

        ['var1=yes', 'var2=1.2', 'var3=40', 'var4=someoption']

    :return: Parsed option. Keys are verified safe for passing as keyword
     arguments and values are "autocasted" to a Python datatype. Declaration
     order is respected, so latest options will override the first ones. Using
     the above example, returned options will be:

     .. code-block:: python3

        OrderedDict([
            ('var1', True),
            ('var2', 1.2),
            ('var3', 40),
            ('var4', 'someoption'),
        ])

    :rtype: OrderedDict

    :raises: InvalidArgument if options have a syntax issue.
    """
    options = OrderedDict()
    if not raw:
        return options

    for option in raw:

        if '=' not in option:
            raise InvalidArgument(
                'Invalid option "{}", options must follow '
                'the syntax "<option_name>=<value>"'.format(option)
            )

        key, value = option.split('=', 1)

        # Check key form
        if not REGEX_SLUG.match(key):
            raise InvalidArgument(
                'Option "{}" is invalid. It must match "{}"'.format(
                    key, REGEX_SLUG.pattern,
                )
            )
        key = key.replace('-', '_')

        # Try to cast value
        for caster in [
            int,
            float,
            booleanize,
        ]:
            try:
                value = caster(value)
                break
            except Exception:
                continue

        options[key] = value

    return options


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
        raise InvalidArgument(
            'No such file {}'.format(args.topology)
        )
    args.topology = abspath(args.topology)

    # Verify inject file exists
    if args.inject:
        if not isfile(args.inject):
            raise InvalidArgument(
                'No such file {}'.format(args.inject)
            )
        args.inject = abspath(args.inject)

    # Determine log directory and create it if required
    if args.log_dir:
        if not isabs(args.log_dir):
            args.log_dir = join(abspath(getcwd()), args.log_dir)
        makedirs(args.log_dir, exist_ok=True)

    # Parse options
    if args.options:
        args.options = parse_options(args.options)
        log.debug('Options given:\n{}'.format(pformat(args.options)))

    return args


def parse_args(argv=None):
    """
    Argument parsing routine.

    :param list argv: A list of argument strings.

    :return: A parsed and verified arguments namespace.
    :rtype: :py:class:`argparse.Namespace`
    """

    parser = ArgumentParser(
        description=(
            'Topology is a framework for building and testing network '
            'topologies, with support for pytest.'
        )
    )
    parser.register('action', 'extend', ExtendAction)

    # Standard options
    parser.add_argument(
        '-v', '--verbose',
        help='Increase verbosity level',
        default=0,
        action='count'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Topology Framework v{}'.format(__version__)
    )

    # Platforms options
    parser.add_argument(
        '--platform',
        default=DEFAULT_PLATFORM,
        help='Platform engine to build the topology with',
        choices=platforms()
    )
    parser.add_argument(
        '-o', '--option',
        nargs='+',
        dest='options',
        action='extend',
        help='Platform options'
    )

    # Ploting options
    parser.add_argument(
        '--plot-dir',
        default=None,
        help=(
            'Obsolete. No longer supported. Used in previous versions of '
            'topology to specify the directory to autoplot topologies'
        )
    )
    parser.add_argument(
        '--plot-format',
        default='svg',
        help=(
            'Obsolete. No longer supported. Used in previous versions of '
            'topology to specify the plot format'
        )
    )

    # Export options
    parser.add_argument(
        '--nml-dir',
        default=None,
        help=(
            'Obsolete. No longer supported. Used in previous versions of '
            'topology to specify the directory to export topologies as NML XML'
        )
    )

    # Logging options
    parser.add_argument(
        '--log-dir',
        default=None,
        help='Directory to create log files'
    )
    parser.add_argument(
        '--show-build-commands',
        help='Show commands executed in nodes during build',
        action='store_true'
    )

    # Building options
    parser.add_argument(
        '--inject',
        default=None,
        help='Path to an attributes injection file'
    )
    parser.add_argument(
        '--non-interactive',
        help='Just build the topology and exit',
        action='store_true'
    )
    parser.add_argument(
        'topology',
        help='File with the topology description to build'
    )

    args = parser.parse_args(argv)
    args = validate_args(args)
    return args


__all__ = [
    'InvalidArgument',
    'parse_options',
    'parse_args',
]
