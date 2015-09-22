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
topology libraries manager module.

This module finds out which topology communication libraries plugins are
installed and returns them in a dictionary.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from copy import copy
from inspect import isfunction
from traceback import format_exc

from pkg_resources import iter_entry_points


log = logging.getLogger(__name__)


def libraries(cache=True):
    """
    List all available communication libraries.

    This function list all communication libraries it can discover looking up
    the entry point. This lookup requires to load all available communication
    libraries plugins, which can be costly or error prone if a plugin
    misbehave, and because of this a cache is stored after the first call.

    :param bool cache: If ``True`` return the cached result. If ``False`` force
     reload of all communication libraries registered for the entry point.
    :rtype: dict
    :return: A dictionary associating the name of the communication library and
     it functions registry:

     ::

        {
            'comm1': [function_a, function_b],
            'my_lib': [my_function_a, another_function]
        }
    """

    # Return cached value if call is repeated
    if cache and hasattr(libraries, 'available'):
        return libraries.available

    # Add default plugins
    # Note: None so far
    available = {}

    # Iterate over entry points
    for ep in iter_entry_points(group='topology_library_10'):

        name = ep.name

        try:
            registry = ep.load()
        except:
            log.error(
                'Unable to load topology communication '
                'library plugin {}.'.format(name)
            )
            log.debug(format_exc())
            continue

        # Validate registry
        if not hasattr(registry, '__iter__'):
            log.error(
                'Ignoring library "{}" as it doesn\'t '
                'match the required interface: '
                'Registry is not iterable.'.format(name)
            )
            continue

        # Validate registers
        invalid = [
            (idx, func) for idx, func in enumerate(registry)
            if not isfunction(func)
        ]
        if invalid:
            log.error(
                'Ignoring library "{}". '
                'Registers are not functions: {}.'.format(
                    name,
                    ', '.join(['{}:{}'.format(*tup) for tup in invalid])
                )
            )
            continue

        available[name] = copy(registry)

    libraries.available = available
    return available


__all__ = ['libraries']
