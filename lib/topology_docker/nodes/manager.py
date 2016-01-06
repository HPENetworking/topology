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
topology_docker nodes manager module.

This module finds out which docker nodes plugins are installed and returns them
in a dictionary.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from inspect import isclass
from traceback import format_exc
from collections import OrderedDict

from pkg_resources import iter_entry_points

from ..node import DockerNode


log = logging.getLogger(__name__)


def nodes(cache=True):
    """
    List all available nodes types.

    This function lists all available node types by discovering installed
    plugins registered in the entry point. This can be costly or error prone if
    a plugin misbehave. Because of this a cache is stored after the first call.

    :param bool cache: If ``True`` return the cached result. If ``False`` force
     reload of all plugins registered for the entry point.
    :rtype: dict
    :return: A dictionary associating the name of the node type and the class
     (subclass of :class:`topology_docker.platform.DockerNode`)
     implementing it:

     ::

        {
            'host': DockerNode,
            'openswitch': OpenSwitchNode
        }
    """

    # Return cached value if call is repeated
    if cache and hasattr(nodes, 'available'):
        return nodes.available

    # Add built-in node types
    available = OrderedDict()

    # Iterate over entry points
    for ep in iter_entry_points(group='topology_docker_node_10'):

        name = ep.name

        try:
            node = ep.load()
        except:
            log.error(
                'Unable to load node from plugin {}'.format(name)
            )
            log.debug(format_exc())
            continue

        if not isclass(node) or not issubclass(node, DockerNode):
            log.error(
                'Ignoring node "{}" as it doesn\'t '
                'match the required interface: '
                'Node not a subclass of DockerNode.'.format(name)
            )
            continue

        available[name] = node

    nodes.available = available
    return available


__all__ = ['nodes']
