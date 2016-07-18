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
Base platform engine module for topology.

This module defines the functionality that a topology platform plugin must
provide to be able to create a network using specific hardware or software.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from abc import ABCMeta, abstractmethod

from six import add_metaclass


log = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class BasePlatform(object):
    """
    Base platform engine class.

    This class represent the base interface that topology engines require to
    implement.

    See the :doc:`Plugins Development Guide </plugins>` for reference.

    :param str timestamp: Timestamp in ISO 8601 format.
    :param nmlmanager: Manager holding the NML namespace.
    :type nmlmanager: :class:`pynml.manager.NMLManager`
    """

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

    @abstractmethod
    def add_node(self, node):
        """
        Add a node to your platform.

        This method receives a NML node and must return a new Engine Node
        subclass of :class:`BaseNode` that implements the communication
        mechanism with that node.

        :param node: The specification NML node to add to the platform.
        :type node: :class:`pynml.nml.Node`
        :rtype: BaseNode
        :return: Platform specific communication node.
        """

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
        :rtype: str
        :return: Real name of the port in the node. This real will be used to
         populate an internal map between the specification name of the port
         and the real name, which can be used to reference the port in commands
         without knowing it's real name in advance.
        """

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

    @abstractmethod
    def post_build(self):
        """
        Postamble hook.

        This hook is called at the last stage of the topology build.
        Use it to setup any final requirements or start any service before
        using the topology.
        """

    @abstractmethod
    def destroy(self):
        """
        Platform destruction hook.

        Use this to remove all elements from the platform, perform any clean
        and return resources.
        """

    @abstractmethod
    def rollback(self, stage, enodes, exception):
        """
        Platform rollback hook.

        This is called when the build fails, possibly by an exception raised in
        previous hooks.

        :param str stage: The stage the build failed. One of:
         - ``pre_build``.
         - ``add_node``.
         - ``add_biport``.
         - ``add_bilink``.
         - ``post_build``.
        :param enodes: Engine nodes already registered.
        :type enodes: OrderedDict of subclasses of :class:`BaseNode`
        :param Exception exception: The exception caught during build failure.
        """

    @abstractmethod
    def relink(self, link_id):
        """
        Relink back a link specified in the topology.

        :param str link_id: Link identifier to be recreated.
        """

    @abstractmethod
    def unlink(self, link_id):
        """
        Unlink (break) a link specified in the topology.

        :param str link_id: Link identifier to be undone.
        """


__all__ = ['BasePlatform']
