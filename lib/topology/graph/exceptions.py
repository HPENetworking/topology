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


class TopologyError(RuntimeError):
    """
    Base class for all topology errors.
    """
    pass


class NotFound(TopologyError):
    """
    Raised when a node or link is not found.
    """
    pass


class AlreadyExists(TopologyError):
    """
    Raised when a node or link already exists.
    """
    pass


class Inconsistent(TopologyError):
    """
    Raised when there are inconsistencies in the topology.
    """
    pass


__all__ = ['TopologyError', 'NotFound', 'AlreadyExists', 'Inconsistent']
