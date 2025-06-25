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
Topology Graph Link module.
"""

from copy import deepcopy

from pprintpp import pformat

from .node import Node
from .port import Port


class Link:
    """
    Topology Graph Link.

    :param str node1: The first node of the link.
    :param str node2: The second node of the link.
    :param str port1: The first port of the link.
    :param str port2: The second port of the link.
    :param dict metadata: The metadata of the link.
    """

    def __init__(
        self,
        node1: Node,
        port1: Port,
        node2: Node,
        port2: Port,
        metadata: dict = None
    ):
        self._node1 = node1
        self._node2 = node2
        self._port1 = port1
        self._port2 = port2
        self._metadata = {} if metadata is None else metadata

        # Allow to override the identifier of the link.
        self.identifier = self.metadata.pop(
            'identifier',
            Link.calc_id(
                node1.identifier,
                port1.label,
                node2.identifier,
                port2.label
            )
        )
        self.attrs = {}

    def as_dict(self) -> dict:
        """
        Returns the link as a dictionary.
        """
        return {
            'node1': self._node1.as_dict(),
            'port1': self._port1.as_dict(),
            'node2': self._node2.as_dict(),
            'port2': self._port2.as_dict(),
            'metadata': deepcopy(self._metadata)
        }

    def __str__(self):
        return pformat(self.as_dict())

    @classmethod
    def calc_id(
        cls,
        node1_id: str,
        port1_label: str,
        node2_id: str,
        port2_label: str
    ) -> str:
        """
        Calculates the identifier of the link.
        :param str node1_id: The identifier of the first node.
        :param str port1_label: The label of the first port.
        :param str node2_id: The identifier of the second node.
        :param str port2_label: The label of the second port.
        """
        port1_id = Port.calc_id(node1_id, port1_label)
        port2_id = Port.calc_id(node2_id, port2_label)

        # Any pair of ports produce the same identifier regardless their order.
        return (
            f'{port1_id} -- {port2_id}'
            if port1_id <= port2_id else
            f'{port2_id} -- {port1_id}'
        )

    @property
    def node1(self) -> Node:
        """
        Returns the first node of the link.
        """
        return self._node1

    @property
    def node2(self) -> Node:
        """
        Returns the second node of the link.
        """
        return self._node2

    @property
    def port1(self) -> Port:
        """
        Returns the first port of the link.
        """
        return self._port1

    @property
    def port2(self) -> Port:
        """
        Returns the second port of the link.
        """
        return self._port2

    @property
    def metadata(self) -> dict:
        """
        Returns the metadata of the link.
        """
        return self._metadata

    def has_node(self, node_id: str) -> bool:
        """
        Returns True if the link has the node.

        :param str node_id: The identifier of the node.
        """
        return (
            self.node1.identifier == node_id or
            self.node2.identifier == node_id
        )

    def has_port(self, node_id: str, port_label: str) -> bool:
        """
        Returns True if the link has the port.

        :param str node_id: The identifier of the node.
        :param str port_label: The port label.
        """
        return (
            self.port1.identifier == Port.calc_id(node_id, port_label) or
            self.port2.identifier == Port.calc_id(node_id, port_label)
        )


__all__ = ['Link']
