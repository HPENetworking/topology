# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2025 Hewlett Packard Enterprise Development LP
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
topology platforms manager module.

This module finds out which topology platforms plugins are installed and
returns them in a dictionary.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from inspect import isclass

import sys
if sys.version_info >= (3, 9):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points  # backport for Python < 3.8

from .platform import BasePlatform


log = logging.getLogger(__name__)


DEFAULT_PLATFORM = 'debug'
"""
Default platform engine.
"""


def platforms(cache=True):
    """
    List all available platform engines.

    This function lists the default engine plus any other it can discover
    looking up the entry point.

    :param bool cache: If ``True`` return the cached result. If ``False`` force
     lookup for plugins registered for the entry point.
    :rtype: list
    :return: A sorted list with all available platforms.
    """

    # Return cached value if call is repeated
    if cache and hasattr(platforms, 'available'):
        return list(platforms.available)

    # Add default plugin
    available = []

    # Iterate over entry points
    for ep in entry_points(group='topology_platform_10'):
        available.append(ep.name)

    available.sort()
    platforms.available = available

    return list(available)


def load_platform(name):
    """
    Load platform identified by given name.

    :param str name: Name of the platform.
     This must be a name available in the list returned by :func:`platforms`.
    :rtype: A :class:`BasePlatform` subclass
    :return: The implementation class on the platform engine.
    """
    if name not in platforms():
        raise RuntimeError('Unknown platform engine "{}".'.format(name))

    # Iterate over entry points
    for ep in entry_points(group='topology_platform_10', name=name):

        try:
            platform = ep.load()
        except Exception as e:
            log.error(
                'Unable to load topology engine '
                'platform plugin {}.'.format(name)
            )
            raise e

        if not isclass(platform) or not issubclass(platform, BasePlatform):
            log.error(
                'Platform "{}" doesn\'t implement the required interface: '
                'Platform not a subclass of BasePlatform.'.format(name)
            )
            continue

        return platform

    raise RuntimeError(
        'Platform engine "{}"" not in entry points.'.format(name)
    )


__all__ = ['platforms', 'load_platform', 'DEFAULT_PLATFORM']
