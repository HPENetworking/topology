# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2024 Hewlett Packard Enterprise Development LP
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
Debug platform engine module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from datetime import datetime

from .node import CommonNode
from .platform import BasePlatform


log = logging.getLogger(__name__)


class DebugPlatform(BasePlatform):
    """
    Plugin to build a topology for debugging.

    See :class:`topology.platforms.platform.BasePlatform` for more information.
    """

    def __init__(self, timestamp, graph, **kwargs):
        super(DebugPlatform, self).__init__(
            timestamp, graph, **kwargs
        )
        self.debug_value = 'fordebug'

    def resolve(self):
        """
        See :meth:`BasePlatform.resolve` for more information.
        """
        log.debug('[HOOK] resolve')

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """
        log.debug('[HOOK] pre_build')

    def add_node(self, node):
        """
        See :meth:`BasePlatform.add_node` for more information.
        """
        log.debug('[HOOK] add_node({})'.format(
            node
        ))
        return DebugNode(node.identifier, **node.metadata)

    def add_biport(self, node, biport):
        """
        See :meth:`BasePlatform.add_biport` for more information.
        """
        log.debug('[HOOK] add_biport({}, {})'.format(
            node, biport
        ))
        return biport.metadata.get('label', biport.identifier)

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        See :meth:`BasePlatform.add_bilink` for more information.
        """
        log.debug('[HOOK] add_bilink({}, {}, {})'.format(
            nodeport_a, nodeport_b, bilink
        ))

    def post_build(self):
        """
        See :meth:`BasePlatform.post_build` for more information.
        """
        log.debug('[HOOK] post_build()')

    def destroy(self):
        """
        See :meth:`BasePlatform.destroy` for more information.
        """
        log.debug('[HOOK] destroy()')

    def rollback(self, stage, enodes, exception):
        """
        See :meth:`BasePlatform.rollback` for more information.
        """
        log.debug('[HOOK] rollback({}, {}, {})'.format(
            stage, enodes, exception
        ))

    def relink(self, link_id):
        """
        See :meth:`BasePlatform.relink` for more information.
        """
        log.debug('[CALL] relink({})'.format(
            link_id
        ))

    def unlink(self, link_id):
        """
        See :meth:`BasePlatform.unlink` for more information.
        """
        log.debug('[CALL] unlink({})'.format(
            link_id
        ))


class DebugNode(CommonNode):
    """
    Engine Node for debugging.
    """

    def __init__(self, identifier, **kwargs):
        super(DebugNode, self).__init__(identifier, **kwargs)

    def send_command(self, cmd, shell=None, silent=False):
        """
        Implementation of the ``send_command`` interface.

        This test node will just echo the command.

        See :meth:`CommonNode.send_command` for more information.
        """
        log.debug('{} [{}].send_command(\'{}\', shell=\'{}\') ::'.format(
            datetime.now().isoformat(), str(self), cmd, shell
        ))
        return cmd

    def _get_services_address(self):
        """
        Implementation of the ``_get_services_address`` interface.

        This test node will return '127.0.0.1'.

        See :meth:`CommonNode._get_services_address` for more information.
        """
        return '127.0.0.1'

    def __str__(self):
        return 'DebugNode(identifier={}, metadata={})'.format(
            self.identifier, self.metadata
        )


__all__ = ['DebugPlatform', 'DebugNode']
