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
topology platforms manager module.

This module finds out which topology platforms plugins are installed and
returns them in a dictionary.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from inspect import isclass
from traceback import format_exc

from pkg_resources import iter_entry_points

from .base import BasePlatform
from .mininet import MininetPlatform


log = logging.getLogger(__name__)


def platforms(cache=True):

    # Return cached value if call is repeated
    if cache and hasattr(platforms, 'available'):
        return platforms.available

    # Add default plugin
    available = {
        'mininet': MininetPlatform
    }

    # Iterate over entry points
    for ep in iter_entry_points(group='topology_platform_ep'):

        name = ep.name

        try:
            platform = ep.load()
        except:
            log.error('Unable to load topology plugin {}.'.format(name))
            log.debug(format_exc())
            continue

        if not isclass(platform) or not issubclass(platform, BasePlatform):
            log.error(
                'Ignoring platform "{}" as it doesn\'t '
                'match the required interface.'.format(name)
            )
            continue

        available[name] = platform

    platforms.available = available
    return available


__all__ = ['platforms']
