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
    :param graph: Topology Graph.
    :type graph: :class:`topology.graph.TopologyGraph`
    """

    @abstractmethod
    def __init__(self, timestamp, graph, **kwargs):
        super(BasePlatform, self).__init__()

    def resolve(self):
        """
        Resolve the topology.

        This method is called after the platform is created and before the
        build process starts. It should resolve the topology graph, making sure
        all nodes, ports and links are correctly defined and all requirements
        are satisfied. If the graph is not resolvable, this method should raise
        an exception.
        """

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

        This method receives a Topology Graph node and must return a new
        Engine Node subclass of :class:`BaseNode` that implements the
        communication mechanism with that node.

        :param node: The Topology Graph node to add to the platform.
        :type node: :class:`topology.graph.Node`
        :rtype: BaseNode
        :return: Platform specific communication node.
        """

    @abstractmethod
    def add_biport(self, node, port):
        """
        Add a bidirectional port to the given node.

        This method receives a Topology Graph node and a port that
        specifies the port required to be added. This methods returns nothing
        as the topology users don't expect to deal directly with ports. All
        interaction is done with the nodes.

        :param node: Topology Graph Node owner of the port, holding the node
         metadata.
        :type node: :class:`topology.graph.Node`
        :param port: The Topology Graph Port holding the port metadata.
        :type biport: :class:`topology.graph.BidirectionalPort`
        :rtype: str
        :return: Real name of the port in the node. This real will be used to
         populate an internal map between the specification name of the port
         and the real name, which can be used to reference the port in commands
         without knowing it's real name in advance.
        """

    @abstractmethod
    def add_bilink(self, nodeport_a, nodeport_b, link):
        """
        Add a link between given nodes and ports.

        This method receives two tuples with the nodes and ports associated
        with the link and the link object to be added to the platform.

        Notice the ``nodeport_a`` and ``nodeport_b`` are passed for backwards
        compatibility. However, now the link object contains the ports and
        nodes associated to the link, so newer platform implementations could
        just ignore ``nodeport_a`` and ``nodeport_b``.

        :param nodeport_a: A tuple (Node, Port) of the first endpoint.
        :type nodeport_a:
         (:class:`topology.graph.Node`, :class:`topology.graph.Port`)
        :param nodeport_b: A tuple (Node, Port) of the second endpoint.
        :type nodeport_b:
         (:class:`topology.graph.Node`, :class:`topology.graph.Port`)
        :param link: The Topology Graph Link.
        :type link: :class:`topology.graph.Link`
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
