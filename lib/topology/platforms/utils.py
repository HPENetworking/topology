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
Common utilities for engine platforms.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from copy import copy
from inspect import isclass
from traceback import format_exc
from collections import OrderedDict

import sys
if sys.version_info >= (3, 9):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points  # backport for Python < 3.8

from .node import BaseNode


log = logging.getLogger(__name__)


class NodeLoader(object):
    """
    Node loader utility class for platform engines.

    This class allows to load nodes for a platform engine using Python entry
    points.

    :param str engine_name: Name of the engine.
    :param str api_version: Version of the API for that engine node.
    :param class base_class: Base class to check against. Any class specified
     here must comply with the :class:`BaseNode`.
    """

    def __init__(self, engine_name, api_version='1.0', base_class=None):
        super(NodeLoader, self).__init__()

        self.entrypoint = 'topology_{engine_name}_node_{api_version}'.format(
            engine_name=engine_name, api_version=api_version.replace('.', '')
        )

        self.base_class = base_class or BaseNode
        assert issubclass(self.base_class, BaseNode)

        self._nodes_cache = OrderedDict()

    def __call__(self, cache=True):
        return self.load_nodes(cache=cache)

    def load_nodes(self, cache=True):
        """
        List all available nodes types.

        This function lists all available node types by discovering installed
        plugins registered in the entry point. This can be costly or error
        prone if a plugin misbehave. Because of this a cache is stored after
        the first call.

        :param bool cache: If ``True`` return the cached result. If ``False``
         force reload of all plugins registered for the entry point.
        :rtype: OrderedDict
        :return: An ordered dictionary associating the name of the node type
         and the class (subclass of :class:`topology.platforms.node.BaseNode`)
         implementing it.
        """

        # Return cached value if call is repeated
        if cache and self._nodes_cache:
            return copy(self._nodes_cache)

        # Add built-in node types
        available = OrderedDict()

        # Iterate over entry points
        for ep in entry_points(group=self.entrypoint):

            name = ep.name

            try:
                node = ep.load()
            except Exception:
                log.exception(
                    'Unable to load node from plugin {}'.format(name)
                )
                log.debug(format_exc())
                continue

            if not isclass(node) or not issubclass(node, self.base_class):
                log.error(
                    'Ignoring node "{}" as it doesn\'t '
                    'match the required interface: '
                    'Node not a subclass of {}.'.format(
                        name, self.base_class.__name__
                    )
                )
                continue

            available[name] = node

        self._nodes_cache = available
        return copy(self._nodes_cache)


__all__ = ['NodeLoader']
