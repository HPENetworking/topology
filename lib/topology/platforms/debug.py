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
Debug platform engine module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging

from .base import BasePlatform, CommonNode


log = logging.getLogger(__name__)


class DebugPlatform(BasePlatform):
    """
    Plugin to build a topology for debugging.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):
        super(DebugPlatform, self).__init__(timestamp, nmlmanager)

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
        return DebugNode(node.identifier, name=node.name, **node.metadata)

    def add_biport(self, node, biport):
        """
        See :meth:`BasePlatform.add_biport` for more information.
        """
        log.debug('[HOOK] add_biport({}, {})'.format(
            node, biport
        ))
        if 'label' in biport.metadata:
            return biport.metadata['label']
        return biport.identifier

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

        See :meth:`topology.platforms.base.CommonNode.send_command` for more
        information.
        """
        log.debug('{}.send_command({}, shell={})'.format(
            str(self), cmd, shell
        ))
        return cmd

    def available_shells(self):
        """
        Implementation of the ``available_shells`` interface.

        This test node has no shells available.

        See :meth:`topology.platforms.base.CommonNode.available_shells` for
        more information.
        """
        log.debug('{}.available_shells()'.format(str(self)))
        return []

    def send_data(self, data, function=None):
        """
        Implementation of the ``send_data`` interface.

        See :meth:`topology.platforms.base.CommonNode.send_data` for more
        information.
        """
        log.debug('{}.send_data({}, data={}, function={})'.format(
            str(self), data, function
        ))
        return super(DebugNode, self).send_data(data, function=function)

    def available_functions(self):
        """
        Implementation of the ``available_functions`` interface.

        See :meth:`topology.platforms.base.CommonNode.available_functions` for
        more information.
        """
        log.debug('{}.available_functions()'.format(str(self)))
        return super(DebugNode, self).available_functions()

    def __str__(self):
        return 'DebugNode(identifier={}, metadata={})'.format(
            self.identifier, self.metadata
        )


__all__ = ['DebugPlatform', 'DebugNode']
