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

This module defines the functionality that a Topology Engine Node must
implement to be able to create a network using a specific environment.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from abc import ABCMeta

from six import add_metaclass

from .elements import BaseElement, CommonElement


log = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class BaseLink(BaseElement):
    """
    FIXME: Document this.
    """


@add_metaclass(ABCMeta)
class CommonLink(CommonElement):
    """
    FIXME: Document this.
    """


__all__ = [
    'BaseLink',
    'CommonLink'
]
