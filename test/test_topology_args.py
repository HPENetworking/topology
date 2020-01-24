# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Hewlett Packard Enterprise Development LP
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
Test suite for module topology.args.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from collections import OrderedDict

import pytest  # noqa
from deepdiff import DeepDiff

from topology.args import parse_args, InvalidArgument


def setup_module(module):
    print('setup_module({})'.format(module.__name__))


def teardown_module(module):
    print('teardown_module({})'.format(module.__name__))


def test_args(tmpdir):

    with pytest.raises(InvalidArgument):
        parse_args(['/this/doesnt/exists.szn'])

    topology = tmpdir.join('topology.szn')
    topology.write('')

    parsed = parse_args([str(topology)])
    assert parsed.verbose == 0

    parsed = parse_args(['-v', str(topology)])
    assert parsed.verbose == 1

    parsed = parse_args(['-vv', str(topology)])
    assert parsed.verbose == 2

    parsed = parse_args(['-vvv', str(topology)])
    assert parsed.verbose == 3

    # Validate option parsing
    with pytest.raises(InvalidArgument):
        parsed = parse_args([
            str(topology),
            '--option', '1argument=100',
        ])

    with pytest.raises(InvalidArgument):
        parsed = parse_args([
            str(topology),
            '--option', '$argument=100',
        ])

    parsed = parse_args([
        str(topology),
        '--option', 'var-1=Yes', 'var2=no', 'var_3=TRUE', 'var4=100',
        '--option', 'var4=200', 'var5=helloworld', 'var6=/tmp/a/path',
        '--option', 'var7=1.7560',
    ])

    expected = OrderedDict([
        ('var_1', True),
        ('var2', False),
        ('var_3', True),
        ('var4', 200),
        ('var5', 'helloworld'),
        ('var6', '/tmp/a/path'),
        ('var7', 1.7560),
    ])

    ddiff = DeepDiff(parsed.options, expected)
    assert not ddiff
