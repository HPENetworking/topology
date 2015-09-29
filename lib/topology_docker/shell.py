# -*- coding: utf-8 -*-
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
Docker shell helper class module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from time import sleep

from pexpect import spawn


class DockerShell(object):
    """
    """

    def __init__(
            self, container, shell, prompt,
            delay=0.2, timeout=None, encoding='utf-8'):
        self._container = container
        self._shell = shell
        self._prompt = prompt
        self._delay = delay
        self._timeout = timeout or -1
        self._encoding = encoding
        self._spawn = spawn(
            'docker exec -i -t {} {}'.format(container, shell)
        )

    def __call__(self, command):
        self._spawn.sendline(command)
        # Without this sleep, the content of .after is truncated most of the
        # time. For bash, the results were:
        # With a value 0.1 the .after content was truncated in 2 of 100 runs.
        # With a value 0.2 the .after content was truncated in 0 of 100 runs.
        sleep(self._delay)
        self._spawn.expect(self._prompt, timeout=self._timeout)
        return self._spawn.after.decode(self._encoding)


__all__ = ['DockerShell']
