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
Deprecated module that once included the classes:

- :class:`topology.platforms.platform.BasePlatform`: Base abstract class to
  implement an engine platform.
- :class:`topology.platforms.node.BaseNode` and
  :class:`topology.platforms.node.CommonNode`: Base abstract classes to
  implement nodes for such engine.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from warnings import warn

from .platform import BasePlatform
from .node import BaseNode, CommonNode


class DeprecatedTopologyModule(UserWarning):
    pass


warn(
    'This module is deprecated, please change all imports from it.\n'
    'topology.platforms.base.BasePlatform => '
    'topology.platforms.platform.BasePlatform\n'
    'topology.platforms.base.BaseNode => '
    'topology.platforms.node.BaseNode\n'
    'topology.platforms.base.CommonNode => '
    'topology.platforms.node.CommonNode\n',
    category=DeprecatedTopologyModule,
)

__all__ = ['BasePlatform', 'BaseNode', 'CommonNode']
__api__ = []
