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
Test suite for module topology.platforms.shell.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

# mock is located in unittest from Python 3.3 onwards, but as an external
# package in Python 2.7, that is why the following is done:
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from topology.platforms.shell import PExpectShell


@patch('topology.platforms.shell.spawn')
def test_spawn_args(mock_spawn):
    """
    Test that the arguments for Pexpect spawn are correct.
    """
    class TestPExpectShell(PExpectShell):
        def _get_connect_command(self):
            return 'test connection command '

    test_shell = TestPExpectShell('')

    test_shell.connect()

    mock_spawn.assert_called_with(
        'test connection command', echo=False, env={'TERM': 'dumb'}
    )

    test_shell = TestPExpectShell(
        '', spawn_args={'env': {'TERM': 'smart'}, 'echo': True}
    )

    test_shell.connect()

    mock_spawn.assert_called_with(
        'test connection command', env={'TERM': 'smart'}, echo=True
    )
