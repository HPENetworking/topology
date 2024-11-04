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
topology shell api module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from warnings import warn
from re import sub as regex_sub
from collections import OrderedDict
from time import sleep
from abc import ABCMeta, abstractmethod

from six import add_metaclass
from pexpect import spawn as Spawn  # noqa
from pexpect import TIMEOUT

from topology.logging import get_logger

TERM_CODES_REGEX = r'\x1B[@-_][0-?]*[ -/]*[@-~]'
"""
Regular expression to match terminal control codes.

A terminal control code is a special sequence of characters that sent by some
applications to control certain features of the terminal. It is responsibility
of the terminal application (driver) to interpret those control codes.
However, when using pexpect, the incoming buffer will still have those control
codes and will not interpret or do anything with them other than store them.
This regular expression allows to remove them as they are unneeded for the
purpose of executing commands and parsing their outputs
(unless proven otherwise).

This pattern works as follows:

``\x1B[@-_]``: Matches the escape character (ASCII code 27) followed by any
character in the range from @ to _.
``[0-?]*``: Matches zero or more characters in the range from 0 to ?.
``[ -/]*``: Matches zero or more characters in the range from space to /.
``[@-~]``: Matches a single character in the range from @ to ~.

This should cover a wide variety of ANSI escape sequences, including those for
text formatting, cursor movement, and other terminal control codes.
"""


class DeprecatedTopologyFunction(UserWarning):
    pass


class NonExistingConnectionError(Exception):
    """
    Exception raised by the shell API when trying to use a non-existent
    connection.
    """
    def __init__(self, connection):
        super(Exception, self).__init__(
            self, 'Non-existing connection {}.'.format(connection)
        )


class AlreadyConnectedError(Exception):
    """
    Exception raised by the shell API when trying to create a connection
    already created.
    """
    def __init__(self, connection):
        super(Exception, self).__init__(
            self, '{} is already connected.'.format(connection)
        )


class AlreadyDisconnectedError(Exception):
    """
    Exception raised by the shell API when trying to disconnect an already
    disconnected connection.
    """
    def __init__(self, connection):
        super(Exception, self).__init__(
            self, '{} is already disconnected.'.format(connection)
        )


class DisconnectedError(Exception):
    """
    Exception raised by the shell API when trying to perform an operation on a
    disconnected connection.
    """
    def __init__(self, connection):
        super(Exception, self).__init__(
            self, '{} is disconnected.'.format(connection)
        )


@add_metaclass(ABCMeta)
class BaseShell(object):
    """
    Base shell class for Topology nodes.

    This class represents a base interface for a Topology node shell. This
    shell is expected to be an interactive shell, where an expect-like
    mechanism is to be used to find a terminal prompt that signals the end of
    the terminal response to a command sent to it.

    Shells of this kind also represent an actual shell in the node. This means
    that one of these objects is expected to exist for every one of the shells
    in the node. These shells are accessible through a *connection* that may be
    implemented using a certain command (``telnet``, or ``ssh``, for example).
    It may be possible to have several connections to the same shell, so these
    shells support multiple connections.

    The behavior that these connections must follow is this one:

    #. New connections to the shell are created by calling the ``connect``
       command of the shell with the name of the connection to be created
       defined in its ``connection`` attribute.
    #. Connections can be disconnected by calling the ``disconnect`` command of
       the shell.
    #. Connections can be either connected or disconnected.
    #. Existing disconnected connections can be connected again by calling the
       ``connnect`` command of the shell.
    #. An attempt to connect an already connected shell or to disconnect an
       already disconnected shell will raise an exception.
    #. These shells will have a *default* connection that will be used if the
       ``connection`` attribute of the shell methods is set to ``None``.
    #. The default connection will be set to ``None`` when the shell is
       initialized.
    #. If the default connection is ``None`` and the ``connect`` command is
       called, it will set the default connection as the connection used in
       this call. Also, if the previous condition is true and if this
       connection attribute is set to ``None``, the name of the default
       connection will be set to '0'.
    #. Every time any operation with the shell is attempted, a connection needs
       to be specified, if this connection is specified to be ``None``, the
       *default* connection of the shell will be used.
    #. If any method other than ``connect`` and ``send_command`` is called with
       a connection that is not defined yet, an exception will be raised.
    #. If ``auto_connect`` is True, calling ``send_command`` with a
       disconnected or nonexistent connection will create and use a new
       connection. An exception will be raised otherwise.

    The behavior of these operations is defined in the following methods,
    implementations of this class are expected to behave as defined here.

    Be aware that the method ``_register_shell`` of the node will add two
    attributes to the shell objects:

    #. ``_name``: name of the shell, the matching key of the node's dictionary
       of shells
    #. ``_node``: node object that holds the shell object

    The ``_register_shell`` method is usually called in the node's'
    ``__init__``.
    """

    @property
    def default_connection(self):
        raise NotImplementedError('default_connection')

    @default_connection.setter
    def default_shell(self, value):
        raise NotImplementedError('default_connection.setter')

    @abstractmethod
    def send_command(
        self, command,
        matches=None, newline=True,
        timeout=None, connection=None, silent=False
    ):
        """
        Send a command to the shell.

        :param str command: Command to be sent to the shell.
        :param list matches: List of strings that may be matched by the shell
         expect-like mechanism as prompts in the command response.
        :param bool newline: True to append a newline at the end of the
         command, False otherwise.
        :param int timeout: Amount of time to wait until a prompt match is
         found in the command response.
        :param str connection: Name of the connection to be used to send the
         command. If not defined, the default connection will be used.
        :param bool silent: True to call the connection logger, False
         otherwise.
        """

    @abstractmethod
    def get_response(self, connection=None, silent=False):
        """
        Get a response from the shell connection.

        This method can be used to add extra processing to the shell response
        if needed, cleaning up terminal control codes is an example.

        :param str connection: Name of the connection to be used to get the
         response from. If not defined, the default connection will be used.
        :param bool silent: True to call the connection logger, False
         otherwise.
        :rtype: str
        :return: Shell response to the previously sent command.
        """

    @abstractmethod
    def is_connected(self, connection=None):
        """
        Shows if the connection to the shell is active.

        :param str connection: Name of the connection to check if connected. If
         not defined, the default connection will be checked.
        :rtype: bool
        :return: True if there is an active connection to the shell, False
         otherwise.
        """

    @abstractmethod
    def connect(self, *args, connection=None, **kwargs):
        """
        Creates a connection to the shell.

        :param str connection: Name of the connection to be created. If not
         defined, an attempt to create the default connection will be done. If
         the default connection is already connected, an exception will be
         raised. If defined in the call but no default connection has been
         defined yet, this connection will become the default one. If the
         connection is already connected, an exception will be raised.
        """

    @abstractmethod
    def disconnect(self, *args, connection=None, **kwargs):
        """
        Terminates a connection to the shell.

        :param str connection: Name of the connection to be disconnected. If
         not defined, the default connection will be disconnected. If the
         default connection is disconnected, no attempt will be done to define
         a new default connection, the user will have to either create a new
         default connection by calling ``connect`` or by defining another
         existing connection as the default one.
        """

    def execute(self, command, *args, connection=None, **kwargs):
        """
        Executes a command.

        If the default connection is not defined, or is disconnected, an
        exception will be raised.

        This is just a convenient method that sends a command to the shell
        using send_command and returns its response using get_response.

        :param str command: Command to be sent.
        :param str connection: Connection to be used to execute this command.
        :rtype: str
        :return: Shell response to the command being sent.
        """
        self.send_command(command, *args, connection=connection, **kwargs)
        return self.get_response(connection=connection)

    def __call__(self, command, *args, connection=None, **kwargs):
        return self.execute(command, *args, connection=connection, **kwargs)

    def _setup_shell(self, *args, connection=None, **kwargs):
        """
        Method called by subclasses that will be triggered after matching the
        initial prompt.

        This method must do a call to expect before it does one to any sending
        call (like send or sendline) and it must do a sending call after the
        last call to expect.

        :param str connection: Name of the connection to be set up. If not
         defined, the default connection will be set up.
        """

    def _register_node(self, node_identifier, shell_name):
        """
        Register the node identifier and the assigned shell name on that node
        in the shell for logging back reference.

        :param str node_identifier: The identifier of the owner node.
        :param str shell_name: Shell name given in the node to this shell.
        """

    def _register_loggers(
        self, node, shell, command_logger=None, response_logger=None
    ):
        """
        Register logger functions for command executions and responses.

        .. warning::

           This function will be removed in future releases.

        :param :class:`topology.base.BaseNode` node: Node that holds this
         shell.
        :param str shell: Name of the shell to show in the sent command log.
        :param function command_logger: Function that logs the command being
         sent. If set to None, the node's _log_command will be used.
        :param function response_logger: Function that logs the command
         response. If set to None, the node's _log_response will be used.
        """


@add_metaclass(ABCMeta)
class PExpectShell(BaseShell):
    """
    Implementation of the BaseShell class using pexpect.

    This class provides a convenient implementation of the BaseShell using
    the pexpect package. The only thing needed for child classes is to define
    the command that will be used to connect to the shell.

    See :class:`BaseShell`.

    :param str prompt: Regular expression that matches the shell prompt.
    :param str initial_command: Command that is to be sent at the beginning of
     the connection.
    :param str initial_prompt: Regular expression that matches the initial
     prompt. This value will be used to match the prompt before calling private
     method ``_setup_shell()``.
    :param str password: Password to be sent at the beginning of the
     connection.
    :param str password_match: Regular expression that matches a password
     prompt.
    :param str prefix: The prefix to be prepended to all commands sent to this
     shell.
    :param int timeout: Default timeout to use in send_command.
    :param str encoding: Character encoding to use when decoding the shell
     response.
    :param bool try_filter_echo: On platforms that doesn't support some way of
     turning off the echo of the command try to filter the echo from the output
     by removing the first line of the output if it match the command.
    :param auto_connect bool: Enable the automatic creation of a connection
     when ``send_command`` is called if the connection does not exist or is
     disconnected.
    :param dict spawn_args: Arguments to be passed to the Pexpect spawn
     constructor. If this is left as ``None``, then
     ``env={'TERM': 'dumb'}, echo=False`` will be passed as keyword
     arguments to the spawn constructor.
    :param str errors: Handling of decoding errors in ``get_response``. The
     values available are the same ones that the ``decode`` method of a bytes
     object expects in its ``error`` keyword argument. Defaults to ``ignore``.
    """

    def __init__(
        self, prompt,
        initial_command=None, initial_prompt=None,
        user=None, user_match='[uU]ser:',
        password=None, password_match='[pP]assword:',
        prefix=None, timeout=None, encoding='utf-8',
        try_filter_echo=True, auto_connect=True,
        spawn_args=None, errors='ignore', **kwargs
    ):

        self._connections = OrderedDict()
        self._default_connection = None

        self._initial_command = initial_command
        self._prompt = prompt
        self._initial_prompt = initial_prompt
        self._user = user
        self._user_match = user_match
        self._password = password
        self._password_match = password_match
        self._prefix = prefix
        # if no timeout is provided use "the default value specified by the
        # class timeout attribute"
        # https://pexpect.readthedocs.io/en/stable/api/pexpect.html#pexpect.spawn.expect
        # which is 30s
        # https://pexpect.readthedocs.io/en/stable/api/pexpect.html#pexpect.spawn
        self._timeout = timeout or -1
        self._encoding = encoding
        self._try_filter_echo = try_filter_echo
        self._auto_connect = auto_connect
        self._command_logger = None
        self._response_logger = None
        self._node_identifier = None
        self._shell_name = None
        self._errors = errors
        self._testlog = None
        self._spawn_args = {
            'env': {'TERM': 'dumb'},
            'echo': False,
            # The use_poll attribute enables using select.poll() over
            # select.select() for socket handling. This is handy if your system
            # could have > 1024 fds
            'use_poll': True,
            **(spawn_args or {})
        }

        self._last_command = None

        # Set the initial prompt not specified
        if self._initial_prompt is None:
            self._initial_prompt = prompt

        super(PExpectShell, self).__init__(**kwargs)

    @property
    def default_connection(self):
        return self._default_connection

    @default_connection.setter
    def default_connection(self, connection):
        if connection not in self._connections:
            raise NonExistingConnectionError(connection)
        self._default_connection = connection

    @abstractmethod
    def _get_connect_command(self):
        """
        Get the command to be used when connecting to the shell.

        This must be defined by any child class as the return value of this
        function will define all the connection details to use when creating a
        connection to the shell. It will be used usually in conjunction with
        other shell attributes to define the exact values to use when creating
        the connection.

        :rtype: str
        :return: The command to be used when connecting to the shell.
        """

    def _get_connection(self, connection=None):
        """
        Get the pexpect object for the given connection name.

        :param str connection: Name of the connection.
        :rtype: :class:`pexpect.spawn`
        :return: The PExpect spawn process that handles the connection.
        """
        connection = connection or self._default_connection or '0'

        if connection not in self._connections:
            raise NonExistingConnectionError(connection)

        return self._connections[connection]

    def send_command(
        self, command,
        matches=None, newline=True,
        timeout=None, connection=None, silent=False, control=False,
        continuous_timeout=False
    ):
        """
        See :meth:`BaseShell.send_command` for more information.

        :param bool control: This is to be used with single character commands
         only. If enabled, the character sent will be interpreted as a control
         character. Enabling this option makes ``newline`` irrelevant. Defaults
         to ``False``.
        :param bool continuous_timeout: if true, we will repeat the expect with
         the same timeout duration as long as the command is still returning
         output.
        """
        # If auto connect is false, fail if:
        # 1. Connection is missing
        # 2. Connection is disconnected
        if not self._auto_connect:
            if not self.is_connected(connection=connection):
                raise DisconnectedError(connection)

        # If auto connect is true, always reconnect unless:
        # 1. Connection already exists, and
        # 2. Connection is connected
        else:
            try:
                if not self.is_connected(connection=connection):
                    self.connect(connection=connection)
            except NonExistingConnectionError:
                self.connect(connection=connection)

        spawn = self._get_connection(connection=connection)

        # Create possible expect matches
        if matches is None:
            matches = [self._prompt]

        # Append prefix if required
        if self._prefix is not None:
            command = '{}{}'.format(self._prefix, command)

        # Save last command in cache to allow to remove echos in get_response()
        self._last_command = command

        # Send line and expect matches
        if control:
            spawn.sendcontrol(command)
        elif newline:
            spawn.sendline(command)
        else:
            spawn.send(command)

        # Log log_send_command
        if not silent:
            if self._testlog:
                self._testlog.log_send_command(
                    self._node_identifier, self._shell_name, command,
                    None if matches == [self._prompt] else matches, timeout)
            else:
                spawn._connection_logger.log_send_command(
                    command, matches, newline, timeout
                )

        # Expect matches
        if timeout is None:
            timeout = self._timeout

        # if continuous_timeout is requested, we will repeat the expect with
        # the same timeout duration as long as the command is still returning
        # output.
        if continuous_timeout:
            buf_length = 0
            while True:
                try:
                    return spawn.expect(matches, timeout=timeout)
                except TIMEOUT as e:
                    if len(spawn.before) > buf_length:
                        buf_length = len(spawn.before)
                    else:
                        raise e
        else:
            match_index = spawn.expect(
                matches, timeout=timeout
            )
            return match_index

    def get_response(self, connection=None, silent=False):
        """
        See :meth:`BaseShell.get_response` for more information.
        """
        # Get connection
        spawn = self._get_connection(connection=connection)

        # Convert binary representation to unicode using encoding
        text = spawn.before.decode(
            encoding=self._encoding, errors=self._errors
        )

        # Remove leading and trailing whitespaces and normalize newlines
        text = text.strip().replace('\r', '')
        term_codes_regex = getattr(
            self, 'TERM_CODES_REGEX', TERM_CODES_REGEX
        )

        # Remove control codes
        text = regex_sub(term_codes_regex, '', text)

        # Split text into lines
        lines = text.splitlines()

        # Delete buffer with output right now, as it can be very large
        del text

        # Remove echo command if it exists
        if self._try_filter_echo and \
                lines and self._last_command is not None \
                and lines[0].strip() == self._last_command.strip():
            lines.pop(0)

        response = '\n'.join(lines)

        # Log response
        if not silent:
            if self._testlog:
                self._testlog.log_get_response(
                    self._node_identifier, self._shell_name, response)
            else:
                spawn._connection_logger.log_get_response(response)

        return response

    def is_connected(self, connection=None):
        """
        See :meth:`BaseShell.is_connected` for more information.
        """
        # Get connection
        spawn = self._get_connection(connection=connection)
        return spawn.isalive()

    def connect(self, *args, connection=None, **kwargs):
        """
        See :meth:`BaseShell.connect` for more information.
        """
        connection = connection or self._default_connection or '0'

        connection_is_present = connection in self._connections

        if connection_is_present and self.is_connected(connection=connection):
            raise AlreadyConnectedError(connection)

        spawn = Spawn(
            self._get_connect_command().strip(),
            **self._spawn_args
        )

        # If the disconnect is called on a connection and then connect is
        # called again on the same connection, this will be called twice,
        # making each message from that connection to be logged twice.
        if connection_is_present:
            present_connection = self._connections[connection]

            spawn.logfile_read = present_connection.logfile_read
            spawn.logfile_send = present_connection.logfile_send
            spawn._connection_logger = present_connection._connection_logger

        else:
            spawn.logfile_read = get_logger(
                OrderedDict([
                    ('node_identifier', self._node_identifier),
                    ('shell_name', self._shell_name),
                    ('connection', connection)
                ]),
                category='pexpect_read',
            )

            spawn.logfile_send = get_logger(
                OrderedDict([
                    ('node_identifier', self._node_identifier),
                    ('shell_name', self._shell_name),
                    ('connection', connection)
                ]),
                category='pexpect_send',
            )

            # Add a connection logger
            # Note: self._node and self._name were added to this shell in the
            #       node's call to its _register_shell method.
            spawn._connection_logger = get_logger(
                OrderedDict([
                    ('node_identifier', self._node_identifier),
                    ('shell_name', self._shell_name),
                    ('connection', connection)
                ]),
                category='connection'
            )
        # Set larger PTTY so there are less unnecessary line
        # changes on the stream
        spawn.setwinsize(30, 150)

        self._connections[connection] = spawn

        try:
            def expect_sendline(prompt, command):
                if command is not None:
                    spawn.expect(
                        prompt, timeout=self._timeout
                    )
                    spawn.sendline(command)

            # If connection is via user
            expect_sendline(self._user_match, self._user)

            # If connection is via password
            expect_sendline(self._password_match, self._password)

            # If connection is via initial command
            expect_sendline(self._initial_prompt, self._initial_command)

            # Setup shell before using it
            self._setup_shell(*args, connection=connection, **kwargs)

            # Wait for command response to match the prompt
            spawn.expect(
                self._prompt, timeout=self._timeout
            )

        except Exception:
            # Always remove a bad connection if it failed
            del self._connections[connection]
            raise

        # Set connection as default connection if required
        if self.default_connection is None:
            self.default_connection = connection

    def disconnect(self, *args, connection=None, **kwargs):
        """
        See :meth:`BaseShell.disconnect` for more information.
        """
        # Get connection
        spawn = self._get_connection(connection=connection)
        if not spawn.isalive():
            raise AlreadyDisconnectedError(connection)
        spawn.close()

    def _register_node(self, node_identifier, shell_name):
        self._node_identifier = node_identifier
        self._shell_name = shell_name

    def _register_loggers(
        self, node, shell, command_logger=None, response_logger=None
    ):

        warn(
            'This method is deprecated, instead of calling _register_loggers '
            'in the shell object, please just call _register_shell in the'
            ' node that holds the shell object.',
            category=DeprecatedTopologyFunction
        )

        self._shell = shell

        if command_logger is None:
            self._command_logger = node._log_command
        else:
            self._command_logger = command_logger

        if response_logger is None:
            self._response_logger = node._log_response
        else:
            self._response_logger = response_logger


class PExpectBashShell(PExpectShell):
    """Custom shell class for Bash.

    This custom base class will setup the prompt ``PS1`` to the
    ``FORCED_PROMPT`` value of the class and will disable the echo of the
    device by issuing the ``stty -echo`` command. All this is done in the
    ``_setup_shell()`` call, which is overriden by this class.

    See :class:`PExpectShell`.

    :param float delay_after_echo_off: Number of seconds pexpect
           should wait after setting echo off before sending another command,
           this allows bash enough time to properly turn echo off.
    """
    FORCED_PROMPT = '@~~==::BASH_PROMPT::==~~@'

    def __init__(
            self,
            initial_prompt=[r'\w+@.+:.+[#$] ', FORCED_PROMPT],
            try_filter_echo=False, delay_after_echo_off=1, **kwargs):

        self._delay_after_echo_off = delay_after_echo_off

        super(PExpectBashShell, self).__init__(
            PExpectBashShell.FORCED_PROMPT,
            initial_prompt=initial_prompt,
            try_filter_echo=try_filter_echo,
            **kwargs
        )

    def _setup_shell(self, *args, connection=None, **kwargs):
        """
        Overriden setup function that will disable the echo on the device on
        the shell and set a pexpect-safe prompt.
        """
        spawn = self._get_connection(connection=connection)

        # Wait initial prompt
        spawn.expect(
            self._initial_prompt, timeout=self._timeout
        )

        # Remove echo
        spawn.sendline('stty -echo')

        # Sleep for a bit to give bash time to turn echo off
        sleep(self._delay_after_echo_off)

        spawn.expect(
            self._initial_prompt, timeout=self._timeout
        )

        # Change prompt to a pexpect secure prompt
        spawn.sendline(
            'export PS1={}'.format(PExpectBashShell.FORCED_PROMPT)
        )
        self._prompt = PExpectBashShell.FORCED_PROMPT


class ShellContext(object):
    """
    Context Manager class for default shell swapping.

    This object will handle the swapping of the default shell when in and out
    of the context.

    :param BaseNode node: Node to default shell to swap.
    :param str shell_to_use: Shell to use during the context session.
    """

    def __init__(self, node, shell_to_use):
        super(ShellContext, self).__init__()
        self._node = node
        self._shell_to_use = shell_to_use
        self._default_shell = node.default_shell

    def __enter__(self):
        self._node.default_shell = self._shell_to_use
        return self._node.get_shell(self._default_shell)

    def __exit__(self, type, value, traceback):
        self._node.default_shell = self._default_shell


__all__ = [
    'TERM_CODES_REGEX',
    'NonExistingConnectionError',
    'AlreadyConnectedError',
    'AlreadyDisconnectedError',
    'BaseShell',
    'PExpectShell',
    'PExpectBashShell',
    'ShellContext'
]
