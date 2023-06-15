# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Hewlett Packard Enterprise Development LP
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
Test suite for the topology executable.
"""

from re import compile
from shutil import which
from sys import executable
from subprocess import run

from topology import __version__


VERSION_REGEX = compile(
    r'.+ v(?P<mayor>\d+)\.(?P<minor>\d+).(?P<rev>\d+)'
)
MAYOR, MINOR, REV = map(int, __version__.split('.'))


def assert_version(stdout):
    match = VERSION_REGEX.match(stdout)
    assert match, (
        f'topology executable stdout {stdout!r} did not match '
        f'expected regex {VERSION_REGEX.pattern!r}'
    )

    groups = match.groupdict()
    mayor, minor, rev = map(int, (
        groups[key] for key in ['mayor', 'minor', 'rev']
    ))

    assert all((
        MAYOR == mayor,
        MINOR == minor,
        REV == rev,
    )), (
        'Version mismatch for the topology executable: '
        f'{MAYOR} != {mayor}?, '
        f'{MINOR} != {minor}?, '
        f'{REV} != {rev}?'
    )


def test_executable():

    # Test first supported call: topology --version
    topology = which('topology')
    assert topology, 'Executable not found'

    completed = run(
        [topology, '--version'],
        encoding='utf-8',
        capture_output=True,
    )
    assert completed.returncode == 0, 'topology executable failed'
    assert_version(completed.stdout)

    # Test second supported call: python3 -m topology --version
    completed = run(
        [executable, '-m', 'topology', '--version'],
        encoding='utf-8',
        capture_output=True,
    )
    assert completed.returncode == 0, 'topology module executable failed'
    assert_version(completed.stdout)
