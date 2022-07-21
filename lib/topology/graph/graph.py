# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Hewlett Packard Enterprise Development LP
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


from copy import deepcopy
from warnings import warn
from typing import Iterator, Tuple

from pprintpp import pformat

from .link import Link
from .node import Node
from .port import Port
from .exceptions import NotFound


class TopologyGraph:
    """
    Represents a topology as a graph.

    :param environment: A dictionary of environment variables.
    """

    def __init__(self, environment: dict = None):
        self._nodes = {}
        self._links = {}
        self._ports = {}
        self.environment = environment if environment is not None else {}

    def as_dict(self) -> dict:
        """
        Returns a dictionary representation of the topology.
        """
        return {
            'nodes': {
                node.identifier: node.as_dict() for node in self.nodes()
            },
            'links': {
                link.identifier: link.as_dict() for link in self.links()
            },
            'ports': {
                port.identifier: port.as_dict() for port in self.ports()
            },
            'environment': deepcopy(self.environment)
        }

    def __str__(self) -> str:
        return pformat(self.as_dict())

    def create_node(
        self, node_id: str, parent: Node = None, **kwargs
    ) -> Node:
        """
        Creates a new node, adds it to the topology and returns it.

        :param node_id: The id of the node to create.
        :param kwargs: The keyword arguments to pass to the node constructor.
        """
        if self.has_node(node_id):
            return self.get_node(node_id)

        node = Node(node_id, parent=parent, metadata=kwargs)
        self._nodes[node.identifier] = node
        return node

    def create_port(self, label: str, node_id: str, **kwargs) -> Port:
        """
        This method does all the following:

        - Creates a new port
        - Adds the port to the topology
        - Adds the port to the node
        - Returns the port

        If the node does not exist, then :class:`NotFound` is raised.

        :param label: The label of the port.
        :param node_id: The id of the node.
        :param kwargs: The keyword arguments to pass to the port constructor.
        """
        if self.has_port_label(node_id, label):
            return self.get_port_by_label(node_id, label)

        node = self.get_node(node_id)

        # Create the port
        port = Port(label, node_id, metadata=kwargs)

        # Add the port to the topology
        self._ports[port.identifier] = port

        # Add the port to the node
        node.add_port(port)

        return port

    def create_link(
        self,
        node1_id: str,
        port1_label: str,
        node2_id: str,
        port2_label: str,
        **kwargs
    ) -> Link:
        """
        Creates a new link and adds it to the topology.

        :param node1_id: The id of the first node.
        :param port1_label: The label of the first port.
        :param node2_id: The id of the second node.
        :param port2_label: The label of the second port.
        :param kwargs: The keyword arguments to pass to the link constructor.
        """
        link_id = Link.calc_id(
            node1_id, port1_label, node2_id, port2_label)

        if self.has_link_id(link_id):
            return self.get_link_by_id(link_id)

        # Get the nodes
        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)

        # Get the ports
        port1 = self.get_port_by_label(node1_id, port1_label)
        port2 = self.get_port_by_label(node2_id, port2_label)

        # Create the link
        link = Link(node1, port1, node2, port2, metadata=kwargs)

        # Add the link to the topology
        self._links[link.identifier] = link

        return link

    def get_node(self, node_id: str) -> Node:
        """
        Returns the node with the given id.

        :param node_id: The id of the node to return.
        """
        if node_id not in self._nodes:
            raise NotFound(f'Node {node_id} not found in the topology')
        return self._nodes[node_id]

    def get_port_by_id(self, port_id: str) -> Port:
        """
        Returns the port with the given id.

        :param port_id: The id of the port to return.
        """
        if port_id not in self._ports:
            raise NotFound(f'Port {port_id} not found in the topology')
        return self._ports[port_id]

    def get_port_by_label(self, node_id: str, port_label: str) -> Port:
        """
        Returns the port with the given label.

        :param node_id: The id of the node.
        :param port_label: The label of the port.
        """
        if node_id not in self._nodes:
            raise NotFound(f'Node {node_id} not found in the topology')
        return self._nodes[node_id].get_port_by_label(port_label)

    def get_link_by_id(self, link_id: str) -> Link:
        """
        Returns the link with the given id.

        :param link_id: The id of the link to return.
        """
        if link_id not in self._links:
            raise NotFound(f'Link {link_id} not found in the topology')
        return self._links[link_id]

    def get_link(
        self,
        node1_id: str,
        port1_label: str,
        node2_id: str,
        port2_label: str
    ) -> Link:
        """
        Returns the link between the given ports.

        :param node1_id: The id of the first node.
        :param port1_label: The label of the first port.
        :param node2_id: The id of the second node.
        :param port2_label: The label of the second port.
        """
        link_id = Link.calc_id(
            node1_id, port1_label, node2_id, port2_label)
        return self.get_link_by_id(link_id)

    def has_node(self, node_id: str) -> bool:
        """
        Returns True if the topology has a node with the given id.

        :param node_id: The id of the node to check.
        """
        return node_id in self._nodes

    def has_port_id(self, port_id: str) -> bool:
        """
        Returns True if the topology has a port with the given id.

        :param port_id: The identifier of the port to check.
        """
        return port_id in self._ports

    def has_port_label(self, node_id: str, port_label: str) -> bool:
        """
        Returns True if the topology has a port with the given label.

        :param node_id: The id of the node.
        :param port_label: The label of the port.
        """
        if node_id not in self._nodes:
            raise NotFound(f'Node {node_id} not found in the topology')
        return self._nodes[node_id].has_port_label(port_label)

    def has_link_id(self, link_id: str) -> bool:
        """
        Returns True if the topology has a link with the given id.

        :param link_id: The id of the link to check.
        """
        return link_id in self._links

    def has_link(
        self,
        node1_id: str,
        port1_label: str,
        node2_id: str,
        port2_label: str
    ) -> bool:
        """
        Returns True if the topology has a link between the given ports.

        :param node1_id: The id of the first node.
        :param port1_label: The label of the first port.
        :param node2_id: The id of the second node.
        :param port2_label: The label of the second port.
        """
        link_id = Link.calc_id(
            node1_id, port1_label, node2_id, port2_label)
        return self.has_link_id(link_id)

    def nodes(self) -> Iterator[Node]:
        """
        Returns an iterator over all nodes in the topology.
        """
        yield from self._nodes.values()

    def ports(self) -> Iterator[Port]:
        """
        Returns an iterator over all ports in the topology.
        """
        yield from self._ports.values()

    def links(self) -> Iterator[Link]:
        """
        Returns an iterator over all links in the topology.
        """
        yield from self._links.values()

    def bilinks(self) -> Iterator[
        Tuple[Tuple[Node, Port],
              Tuple[Node, Port], Link]
    ]:
        """
        Returns an iterator over tuples of the form:
        ((node1, port1), (node2, port2)), link). That is, a 3-tuple where the
        first two elements are 2-tuples of the form (node, port) and the third
        element is the link.

        This method exists for backwards compatibility. Use links() instead.
        """
        warn(
            'TopologyGraph.bilinks() is deprecated. Use links() instead.',
            DeprecationWarning
        )
        for link in self._links.values():
            yield ((link.node1, link.port1), (link.node2, link.port2), link)

    def biports(self) -> Iterator[Tuple[Node, Port]]:
        """
        Returns an iterator over tuples of the form:
        (node, port). That is, a 2-tuple where the first element is the node
        and the second element is the port.

        This method exists for backwards compatibility. Use ports() instead.
        """
        warn(
            'TopologyGraph.biports() is deprecated. Use ports() instead.',
            DeprecationWarning
        )
        for node in self._nodes.values():
            for port in node.ports():
                yield (node, port)

    def check_consistency(self):
        """
        Checks the consistency of the topology which includes:

        - Whenever a node has a parent, that parent must exist, and the parent
          must have the node as a subnode.
        - Whenever a node has a subnode, that subnode must exist.
        - Whenever a link has a node1, that node must exist.
        - Whenever a link has a node2, that node must exist.
        - Whenever a link has a port1, that port must exist in the topology
          and in the node1.
        - Whenever a link has a port2, that port must exist in the topology
          and in the node2.
        """

        # Validate parent/child relationships
        for node in self._nodes.values():
            for subnode in node._subnodes:
                if subnode not in self._nodes:
                    raise NotFound(
                        f'Node {subnode.identifier} which is children of '
                        f'{node.identifier} was not found in the topology')

            if (
                node.parent is not None and
                node.parent.identifier not in self._nodes
            ):
                raise NotFound(
                    f'Node {node.parent.id} which is parent of '
                    f'{self.identifier} was not found in the topology')

        # Validate link/node relationships
        for link in self._links.values():
            if link.node1 not in self.nodes():
                raise NotFound(
                    f'Node {link.node1.identifier} which is node1 of '
                    f'{link.identifier} was not found in the topology')

            if link.node2 not in self.nodes():
                raise NotFound(
                    f'Node {link.node2.identifier} which is node2 of '
                    f'{link.identifier} was not found in the topology')

            if link.port1 not in self.ports():
                raise NotFound(
                    f'Port {link.port1.identifier} which is port1 of '
                    f'{link.identifier} was not found in the topology')

            if link.port2 not in self.ports():
                raise NotFound(
                    f'Port {link.port2.identifier} which is port2 of '
                    f'{link.identifier} was not found in the topology')

            if link.port1 not in link.node1.ports():
                raise NotFound(
                    f'Port {link.port1.identifier} which is port1 of '
                    f'{link.identifier} was not found in the node '
                    f'{link.node1.identifier}')

            if link.port2 not in link.node2.ports():
                raise NotFound(
                    f'Port {link.port2.identifier} which is port2 of '
                    f'{link.identifier} was not found in the node '
                    f'{link.node2.identifier}')


__all__ = ['TopologyGraph']
