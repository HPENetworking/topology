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
Topology Graph port module.
"""


from copy import deepcopy
from pprintpp import pformat


class Port:
    """
    Topology Graph Port.

    :param str label: The label of the port, relative to the node.
    :param str node_id: The identifier of the node.
    :param dict metadata: The metadata of the port.
    """

    def __init__(
        self,
        label: str,
        node_id: str,
        metadata: dict = None
    ):
        self._label = label
        self._node_id = node_id
        self._metadata = {} if metadata is None else metadata
        self._identifier = Port.calc_id(node_id, label)

        # For backwards compatibility:
        self._metadata['label'] = self._label

    def __str__(self):
        return pformat(self.as_dict())

    def as_dict(self) -> dict:
        """
        Returns the port as a dictionary.
        """
        return {
            'identifier': self._identifier,
            'label': self._label,
            'node_id': self._node_id,
            'metadata': deepcopy(self._metadata)
        }

    @property
    def label(self) -> str:
        """
        Returns the readonly label of the port, relative to the node.

        :return: The label of the port.
        :rtype: str
        """
        return self._label

    @property
    def identifier(self) -> str:
        """
        Returns the readonly identifier of the port.
        """
        return self._identifier

    @property
    def metadata(self) -> dict:
        """
        Returns the metadata of the port.
        """
        return self._metadata

    @property
    def node_id(self) -> str:
        """
        Returns the readonly node identifier of the port.
        """
        return self._node_id

    @classmethod
    def calc_id(
        cls,
        node_id: str,
        port_label: str
    ) -> str:
        """
        Calculates the identifier of the port.

        :param str node_id: The identifier of the node.
        :param str port_label: The relative (to the node) name of the port.
        :return: The identifier of the port.
        """
        return f'{node_id}:{port_label}'


__all__ = ['Port']
