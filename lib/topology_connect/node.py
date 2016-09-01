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
topology_connect base node module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from logging import getLogger
from abc import ABCMeta, abstractmethod

from six import add_metaclass

from topology.platforms.node import CommonNode


log = getLogger(__name__)


@add_metaclass(ABCMeta)
class ConnectNode(CommonNode):
    """
    Base node class for Topology Connect.

    See :class:`topology.platform.CommonNode` for more information.
    """

    @abstractmethod
    def __init__(self, identifier, **kwargs):
        super(ConnectNode, self).__init__(identifier, **kwargs)

    @abstractmethod
    def start(self):
        """
        Starts the Node.
        """

    @abstractmethod
    def stop(self):
        """
        Stops the Node.
        """


@add_metaclass(ABCMeta)
class CommonConnectNode(ConnectNode):
    """
    Common Connect Node class for Topology Connect.

    This class will automatically auto-connect to all its shells on start and
    disconnect on stop.

    See :class:`topology_connect.platform.ConnectNode` for more information.
    """

    @abstractmethod
    def __init__(self, identifier, fqdn='127.0.0.1', **kwargs):
        super(CommonConnectNode, self).__init__(identifier, **kwargs)
        self._fqdn = fqdn

    def start(self):
        """
        Connect to all node shells.
        """
        for shell in self._shells.values():
            shell.connect()

    def stop(self):
        """
        Disconnect from  all node shells.
        """
        for shell in self._shells.values():
            shell.disconnect()

    def _get_services_address(self):
        return self._fqdn


__all__ = ['ConnectNode', 'CommonConnectNode']
