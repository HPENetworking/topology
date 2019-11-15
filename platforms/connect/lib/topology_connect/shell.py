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
topology_connect shell management module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import getuid
from pwd import getpwuid
from logging import getLogger
from os.path import isabs, join, expanduser

from topology.platforms.shell import PExpectShell, PExpectBashShell


log = getLogger(__name__)


class SshMixin(object):
    """
    SSH connection mixin for the Topology shell API.

    This class implements a ``_get_connect_command()`` method that allows to
    interact with a shell through an SSH session, and extends the constructor
    to request for SSH related connection parameters.

    The default options will assume that you will be connecting using a SSH
    key (and you seriously SHOULD). If, for some reason, you MUST use a
    password to connect to the shell in question (and DON'T unless absolutely
    required! Like, really, really, DO NOT!) you must set the ``identity_file``
    to ``None`` and set the options to at least have ``BatchMode=no``. Also,
    as expected by the Topology shell low level API you must pass the
    ``password`` (and ``password_match`` if required) to the constructor.

    Note: The constructor of this class should look as follow::

        # Using PEP 3102 -- Keyword-Only Arguments
        def __init__(
            self, *args,
            user=None, hostname='127.0.0.1', port=22,  # noqa
            options=('BatchMode=yes', ), identity_file='id_rsa',
            **kwargs):

    Sadly, this is Python 3 only. Python 2.7 didn't backported this feature.
    So, this is the legacy way to achieve the same goal. Awful, I know :/

    :param str user: User to connect with. If ``None``, the user running the
     process will be used.
    :param str hostname: Hostname or IP to connect to.
    :param int port: SSH port to connect to.
    :param tuple options: SSH options to use.
    :param str identity_file: Absolute or relative (in relation to ``~/.ssh/``)
     path to the private key identity file. If ``None`` is provided, key based
     authentication will not be used.
    """
    def __init__(self, *args, **kwargs):
        self._username = kwargs.pop('user', None)
        self._hostname = kwargs.pop('hostname', '127.0.0.1')
        self._port = kwargs.pop('port', 22)
        self._options = kwargs.pop('options', ('BatchMode=yes', ))
        self._identity_file = kwargs.pop('identity_file', 'id_rsa')

        # Use current user if not specified
        if self._username is None:
            self._username = SshMixin.get_username()

        # Provide a sensible default for the identity file
        if self._identity_file is not None and not isabs(self._identity_file):
            self._identity_file = join(
                expanduser('~/.ssh/'), self._identity_file
            )

        super(SshMixin, self).__init__(*args, **kwargs)

    @staticmethod
    def get_username():
        """
        Get the username.

        :return: The user currently running the process.
        :rtype: str
        """
        return getpwuid(getuid()).pw_name

    def _get_connect_command(self):
        """
        Implementation of the private method defined by the PExpectShell class
        to define the connection command.

        :return: The command that will be used to launch the shell process.
        :rtype: str
        """

        options = ''
        if self._options:
            options = ' -o {}'.format(' -o '.join(self._options))

        if self._identity_file:
            options = ' -i {}{}'.format(self._identity_file, options)

        connect_command = (
            'ssh {self._username}@{self._hostname} '
            '-p {self._port}{options}'.format(
                **locals()
            )
        )
        return connect_command


class TelnetMixin(object):
    """
    Telnet connection mixin for the Topology shell API.

    Note: The constructor of this class should look as follow::

        # Using PEP 3102 -- Keyword-Only Arguments
        def __init__(
            self, *args,
            hostname='127.0.0.1', port=23,
            **kwargs):

    Sadly, this is Python 3 only. Python 2.7 didn't backported this feature.
    So, this is the legacy way to achieve the same goal. Awful, I know :/

    :param str hostname: Hostname or IP to connect to.
    :param int port: Telnet port to connect to.
    """
    def __init__(self, *args, **kwargs):
        self._hostname = kwargs.pop('hostname', '127.0.0.1')
        self._port = kwargs.pop('port', 23)

        super(TelnetMixin, self).__init__(*args, **kwargs)

    def _get_connect_command(self):
        """
        Implementation of the private method defined by the PExpectShell class
        to define the connection command.

        :return: The command that will be used to launch the shell process.
        :rtype: str
        """
        connect_command = (
            'telnet {self._hostname} {self._port}'.format(
                **locals()
            )
        )
        return connect_command


class SshShell(SshMixin, PExpectShell):
    """
    Simple class mixing the pexcept based shell with the SSH mixin.
    """


class TelnetShell(TelnetMixin, PExpectShell):
    """
    Simple class mixing the pexcept based shell with the Telnet mixin.
    """


class SshBashShell(SshMixin, PExpectBashShell):
    """
    Simple class mixing the Bash specialized pexcept based shell with the SSH
    mixin.
    """


class TelnetBashShell(TelnetMixin, PExpectBashShell):
    """
    Simple class mixing the Bash specialized pexcept based shell with the
    Telnet mixin.
    """


__all__ = [
    'SshMixin', 'TelnetMixin',
    'SshShell', 'TelnetShell',
    'SshBashShell', 'TelnetBashShell'
]
