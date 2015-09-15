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
Base engine platform module for topology.

This module defines the functionality that a topology platform plugin must
provide to be able to create a network using specific hardware.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from abc import ABCMeta, abstractmethod


log = logging.getLogger(__name__)


class BasePlatform(object):
    """
    Base engine platform class.

    This class represent the base interface that topology engines require to
    implement.

    :param str timestamp: Timestamp in ISO 8601 format.
    :param nmlmanager: Manager holding the NML namespace.
    :type nmlmanager: :class:`NMLManager`
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, timestamp, nmlmanager):
        pass

    @abstractmethod
    def pre_build(self):
        """
        Preamble hook.

        This hook is called at the first stage of the topology build.
        Use it to setup any requirements your platform has.
        """
        pass

    @abstractmethod
    def add_node(self, node):
        """
        Add a node to your platform.

        This method receives a NML node and must return a new Engine Node
        subclass of :class:`topology.platforms.base.BaseNode` that implements
        the communication mechanism with that node.

        :param node: The specification NML node to add to the platform.
        :type node: :class:`pynml.nml.Node`
        :rtype: :class:`topology.platforms.base.BaseNode`
        :return: Platform specific communication node.
        """
        pass

    @abstractmethod
    def add_biport(self, node, biport):
        """
        Add a bidirectional port to the given node.

        This method receives a NML node and a NML bidirectional port that
        specifies the port required to be added. This methods returns nothing
        as the topology users don't expect to deal directly with ports. All
        interaction is done with the nodes.

        :param node: The specification NML node owner of the port.
        :type node: :class:`pynml.nml.Node`
        :param biport: The specification NMP bidirectional port to add to the
         platform.
        :type biport: :class:`pynml.nml.BidirectionalPort`
        """
        pass

    @abstractmethod
    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a bidirectional link between given nodes and ports.

        This method receives two tuples with the NML nodes and bidirectional
        ports associated with the bidirectional link and also the NML
        bidirectional link object that specifies the link required to be added
        to the platform. This methods returns nothing as the topology users
        don't expect to deal directly with links. All interaction is done with
        the nodes.

        :param nodeport_a: A tuple (Node, BiPort) of the first endpoint.
        :type nodeport_a:
         (:class:`pynml.nml.Node`, :class:`pynml.nml.BidirectionalPort`)
        :param nodeport_b: A tuple (Node, BiPort) of the second endpoint.
        :type nodeport_b:
         (:class:`pynml.nml.Node`, :class:`pynml.nml.BidirectionalPort`)
        :param bilink: The specification NMP bidirectional link to add to the
         platform.
        :type biport: :class:`pynml.nml.BidirectionalLink`
        """
        pass

    @abstractmethod
    def post_build(self):
        """
        Postamble hook.

        This hook is called at the last stage of the topology build.
        Use it to setup any final requirements or start any service before
        using the topology.
        """
        pass

    @abstractmethod
    def destroy(self):
        """
        Platform destruction hook.

        Use this to remove all elements from the platform, perform any clean
        and return resources.
        """
        pass


class BaseNode(object):
    """
    Base engine node class.

    This class represent the base interface that engine nodes require to
    implement.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def send_command(self, cmd, shell=None):
        """
        Send a command to this engine node.

        :param str cmd: Command to send.
        :param str shell: Shell that must interpret the command.
         `None` for the default shell. Is up to the engine platform to
         determine what the default shell is.
        :rtype: str
        :return: The response of the command.
        """

    @abstractmethod
    def send_data(self, data, function=None):
        """
        Send data to a function and return it's result.

        This interface is particularly useful to implement communication with
        this node when the node has a Restful API or other programmatic
        interface. Another option is to provide wrapper functions to
        known CLI commands while implementing parser for their outputs.

        :param dict data: Data to send.
        :param str function: The name of the function to call with data.
         `None` is the default function.Is up to the engine platform to
         determine what the default function is.
        :rtype: dict
        :return: The response of the function.
        """


__all__ = ['BasePlatform', 'BaseNode']
