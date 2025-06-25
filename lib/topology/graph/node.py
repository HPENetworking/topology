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

"""
Topology Graph Node module.
"""


from warnings import warn
from copy import deepcopy
from typing import Iterator

from pprintpp import pformat
from typing_extensions import Self

from .port import Port
from .exceptions import AlreadyExists, Inconsistent, NotFound


class Node:
    """
    Topology Node.

    :param str identifier: The identifier of the node.
    :param Node parent: The parent node.
    :param dict metadata: The metadata of the node.
    """

    def __init__(
        self,
        identifier: str,
        parent: Self = None,
        metadata: dict = None
    ):
        self._identifier = identifier
        self._metadata = {} if metadata is None else metadata
        self._subnodes = {}
        self._ports = {}

        """
        The parent node.
        """
        self.parent = parent

    def as_dict(self) -> dict:
        """
        Returns the node as a dictionary.
        """
        return {
            'identifier': self._identifier,
            'metadata': deepcopy(self._metadata),
            'subnodes': {
                subnode_id: subnode.as_dict()
                for subnode_id, subnode in self._subnodes.items()
            },
            'ports': {
                port_id: port.as_dict()
                for port_id, port in self._ports.items()
            }
        }

    def __str__(self):
        return pformat(self.as_dict())

    @property
    def identifier(self) -> str:
        """
        Returns the readonly identifier of the node.
        """
        return self._identifier

    @property
    def name(self) -> str:
        """
        Returns the name of the node.

        This exists for backwards compatibility. It is recommended to use
        metadata instead.
        """
        warn(
            'Use of GraphNode.name is deprecated. Use metadata.get("name") '
            'instead.',
            DeprecationWarning
        )
        return self._metadata.get('name')

    @property
    def metadata(self) -> dict:
        """
        Returns the metadata of the node.
        """
        return self._metadata

    def has_parent(self) -> bool:
        """
        Returns True if the node has a parent.
        """
        return self.parent is not None

    def add_subnode(self, subnode: Self):
        """
        Adds a subnode to the node.

        :param Node subnode: The subnode to add.
        """
        if subnode.identifier in self._subnodes:
            raise AlreadyExists(
                f'Subnode {subnode.identifier} already exists in node '
                f'{self.identifier}'
            )
        self._subnodes[subnode.identifier] = subnode

    def has_subnode(self, subnode_id: str) -> bool:
        """
        Returns True if the node has a subnode with the given identifier.

        :param str subnode_id: The identifier of the subnode.
        """
        return subnode_id in self._subnodes

    def get_subnode(self, subnode_id: str) -> Self:
        """
        Returns the subnode with the given identifier.

        :param str subnode_id: The identifier of the subnode.
        """
        if subnode_id not in self._subnodes:
            raise NotFound(
                f'Subnode {subnode_id} not found in node '
                f'{self.identifier}'
            )
        return self._subnodes[subnode_id]

    def subnodes(self) -> Iterator[Self]:
        """
        Returns an iterator over all subnodes in the node.
        """
        yield from self._subnodes.values()

    def ports(self) -> Iterator[Port]:
        """
        Returns an iterator over all ports in the node.
        """
        yield from self._ports.values()

    def add_port(self, port: Port):
        """
        Adds a port to the node.

        :param topology.graph.Port port: The port to add.
        """
        if port.node_id != self.identifier:
            raise Inconsistent(
                f'Cannot add port {port.identifier} to node {self.identifier} '
                'because port.node_id points to a different '
                f'node: {port.node_id}'
            )
        if port.identifier in self._ports:
            raise AlreadyExists(
                f'Port {port.identifier} already exists in '
                f'node {self.identifier}')
        self._ports[port.identifier] = port

    def get_port_by_id(self, port_id: str) -> Port:
        """
        Returns the port with the given identifier.

        :param str port_id: The identifier of the port.
        """
        if port_id not in self._ports:
            raise NotFound(
                f'Port {port_id} not found in node {self.identifier}'
            )
        return self._ports[port_id]

    def get_port_by_label(self, port_label: str) -> Port:
        """
        Returns the port with the given label.

        :param str port_label: The label of the port.
        """
        port_id = Port.calc_id(self.identifier, port_label)
        return self.get_port_by_id(port_id)

    def has_port_id(self, port_id: str) -> bool:
        """
        Returns True if the node has a port with the given identifier.

        :param str port_id: The identifier of the port.
        """
        return port_id in self._ports

    def has_port_label(self, port_label: str) -> bool:
        """
        Returns True if the node has a port with the given label.

        :param str port_label: The label of the port.
        """
        port_id = Port.calc_id(self.identifier, port_label)
        return self.has_port_id(port_id)


__all__ = ['Node']
