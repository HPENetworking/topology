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
topology_connect engine platform module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from logging import getLogger

from topology.platforms.base import BasePlatform


log = getLogger(__name__)


class ConnectPlatform(BasePlatform):

    def __init__(self, timestamp, nmlmanager):
        raise NotImplementedError('__init__')

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """
        raise NotImplementedError('pre_build')

    def add_node(self, node):
        """
        See :meth:`BasePlatform.add_node` for more information.
        """
        raise NotImplementedError('add_node')
        return None  # enode

    def add_biport(self, node, biport):
        """
        See :meth:`BasePlatform.add_biport` for more information.
        """
        raise NotImplementedError('add_biport')
        return None  # eport

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        raise NotImplementedError('add_bilink')

    def post_build(self):
        """
        See :meth:`BasePlatform.post_build` for more information.
        """
        raise NotImplementedError('post_build')

    def destroy(self):
        """
        See :meth:`BasePlatform.destroy` for more information.
        """
        raise NotImplementedError('destroy')

    def rollback(self, stage, enodes, exception):
        """
        See :meth:`BasePlatform.rollback` for more information.
        """
        raise NotImplementedError('rollback')

    def relink(self, link_id):
        """
        See :meth:`BasePlatform.relink` for more information.
        """
        raise NotImplementedError('relink')

    def unlink(self, link_id):
        """
        See :meth:`BasePlatform.unlink` for more information.
        """
        raise NotImplementedError('unlink')


__all__ = ['ConnectPlatform']
