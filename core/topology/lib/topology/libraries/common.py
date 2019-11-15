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
Common helpers communication library implementation.

This library defines some helpers as a communication library.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division


def assert_batch(enode, commands, replace=None, shell=None):
    """
    Execute a batch of return-less template commands in the enode shell.

    :param enode:
    :type: topology.platforms.node.BaseNode
    :param str commands: Multiline docstring template with the return-less
     commnads to execute and assert.
    :param dict replace: Namespace to replace tokens in commands.
    :param str shell: Shell name to execute the batch.
    """
    assert commands

    if replace is not None:
        assert isinstance(replace, dict)
        commands = commands.format(**replace)

    for cmd in commands.splitlines():

        # Ignore empty lines in batch
        cmd = cmd.strip()
        if not cmd:
            continue

        # Assert that commands return nothing
        response = enode(cmd, shell=shell)
        assert not response


__all__ = [
    'assert_batch'
]
