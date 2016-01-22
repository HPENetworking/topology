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
Docker shell helper class module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from pexpect import spawn


class DockerShell(object):
    """
    Shell helper class.

    This class wrapps a ``docker exec`` call to a given shell command and
    manages a pexpect spawn object for it.

    It implementes the ``__call__`` method that allows to call the objects
    as it were the contained shell.
    """

    def __init__(
            self, container, shell, prompt,
            prefix=None, timeout=None, encoding='utf-8'):
        self._container = container
        self._shell = shell
        self._prompt = prompt
        self._prefix = prefix
        self._timeout = timeout or -1
        self._encoding = encoding
        self._spawn = None

    def __call__(self, command):

        # Lazy-spawn
        if self._spawn is None:
            self._spawn = spawn(
                'docker exec -i -t {} {}'.format(
                    self._container, self._shell
                ),
                echo=False
            )
            # Cut output at first prompt
            self._spawn.expect(self._prompt, timeout=self._timeout)

        # Prefix command if required
        if self._prefix is not None:
            command = self._prefix + command

        self._spawn.sendline(command)
        self._spawn.expect(self._prompt, timeout=self._timeout)

        # Convert binary representation to unicode using encoding
        raw = self._spawn.before.decode(self._encoding)

        # Remove leading and trailing whitespaces and normalize newlines
        lines = raw.strip().replace('\r', '').splitlines()
        del raw

        # Remove echo command if it exists
        if lines and lines[0].strip() == command.strip():
            lines.pop(0)

        return '\n'.join(lines)


__all__ = ['DockerShell']
