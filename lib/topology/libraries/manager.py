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
topology libraries manager module.

This module finds out which topology communication libraries plugins are
installed and returns them in a dictionary.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from functools import partial
from inspect import isfunction, isclass
from traceback import format_exc
from collections import OrderedDict
from argparse import Namespace

import sys
if sys.version_info >= (3, 9):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points  # backport for Python < 3.8


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
     it functions or classes:

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
    for ep in entry_points(group='topology_library_10'):

        name = ep.name

        try:
            library = ep.load()
        except Exception:
            log.error(
                'Unable to load topology communication '
                'library plugin {}.'.format(name)
            )
            log.debug(format_exc())
            continue

        # Validate library
        if not hasattr(library, '__all__'):
            log.error(
                'Ignoring library "{}" as it doesn\'t '
                'match the required interface: '
                '__all__ is missing.'.format(name)
            )
            continue

        # Validate entities
        invalid = [
            func for func in library.__all__
            if not isfunction(getattr(library, func, None)) and
            not isclass(getattr(library, func, None))
        ]

        if invalid:
            log.error(
                'Ignoring library "{}". '
                'Found non-functions or classes: {}.'.format(
                    name, ', '.join(invalid)
                )
            )
            continue

        available[name] = [
            getattr(library, func, None) for func in library.__all__
        ]

    libraries.available = available
    return available


class LibsProxy(object):
    """
    Proxy object to call communication libraries.

    This proxy object is expected to be used by an engine node to add support
    for communication libraries.

    :param enode: The engine node to communicate with.
    :type enode: topology.platforms.node.BaseNode
    """
    def __init__(self, enode):
        super(LibsProxy, self).__init__()
        self._enode = enode
        self._libraries = OrderedDict()

        for libname, callables in libraries().items():
            # We create a dictionary using dictionary comprehension syntax
            # that will map for each callable in the library the name of
            # such callable with a new partial function that will bind the
            # first argument to the enode. Then, we expand that dictionary and
            # feed it as kwargs to the Namespace class, that will allow us
            # to use the dictionary keys as instance attributes.
            # Very nice Python magic indeed.
            self._libraries[libname] = Namespace(**{
                c.__name__: partial(c, enode) for c in callables
            })

    def __getattr__(self, name):
        if name not in self._libraries:
            raise Exception(
                'Unknown communication library function {}. '
                'Are you missing a dependency?'.format(name)
            )
        return self._libraries[name]


__all__ = ['LibsProxy', 'libraries']
