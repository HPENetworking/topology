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
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, timestamp, nmlmanager):
        pass

    @abstractmethod
    def pre_build(self):
        pass

    @abstractmethod
    def add_node(self, node):
        pass

    @abstractmethod
    def add_biport(self, node, biport):
        pass

    @abstractmethod
    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        pass

    @abstractmethod
    def post_build(self):
        pass

    @abstractmethod
    def destroy(self):
        pass


class BaseNode(object):
    __metaclass__ = ABCMeta


__all__ = ['BasePlatform']
