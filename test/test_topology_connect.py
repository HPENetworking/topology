# -*- coding: utf-8 -*-
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
Test suite for module topology_connect.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import pytest  # noqa

from topology_connect import __version__


def setup_module(module):
    print('setup_module({})'.format(module.__name__))


def teardown_module(module):
    print('teardown_module({})'.format(module.__name__))


def test_semantic_version():
    """
    Check that version follows the Semantic Versioning 2.0.0 specification.

        http://semver.org/
    """
    mayor, minor, rev = map(int, __version__.split('.'))

    assert mayor >= 0
    assert minor >= 0
    assert rev >= 0
