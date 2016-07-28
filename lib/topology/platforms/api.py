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
Base topology element API module for topology.

This module defines several APIs that are used by different topology elements.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from abc import ABCMeta, abstractmethod

from six import add_metaclass


log = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class HighLevelShellAPI(object):
    """
    API used to interact with node shells.

    :var str default_shell: Engine node default shell.
    """

    @property
    def default_shell(self):
        raise NotImplementedError('default_shell')

    @default_shell.setter
    def default_shell(self, value):
        raise NotImplementedError('default_shell.setter')

    @abstractmethod
    def available_shells(self):
        """
        Get the list of available shells.

        :return: The list of all available shells. The first element is the
         default (if any).
        :rtype: List of str.
        """

    @abstractmethod
    def send_command(self, cmd, shell=None, silent=False):
        """
        Send a command to this engine node.

        :param str cmd: Command to send.
        :param str shell: Shell that must interpret the command.
         ``None`` for the default shell. Is up to the engine node to
         determine what its default shell is.
        :param bool silent: If ``False``, print input command and response to
         stdout.

        :return: The response of the command.
        :rtype: str
        """

    def __call__(self, *args, **kwargs):
        return self.send_command(*args, **kwargs)

    @abstractmethod
    def _register_shell(self, name, shellobj):
        """
        Allow plugin developers to register a shell when initializing a node.

        :param str name: Unique name of the shell to register.
        :param shellobj: The shell object to register.
        :type shellobj: BaseShell
        """


@add_metaclass(ABCMeta)
class LowLevelShellAPI(object):
    """
    API used to interact with low level shell objects.
    """

    @abstractmethod
    def use_shell(self, shell):
        """
        Create a context manager that allows to use a different default shell
        in a context, including access to it's low-level shell object.

        :param str shell: The default shell to use in the context.

        Assuming, for example, that a node has two shells:
        ``bash`` and ``python``:

        ::

            with mynode.use_shell('python') as python:
                # This context manager sets the default shell to 'python'
                mynode('from os import getcwd')
                cwd = mynode('print(getcwd())')

                # Access to the low-level shell API
                python.send_command('foo = (', matches=['... '])
                ...
        """

    @abstractmethod
    def get_shell(self, shell):
        """
        Get the shell object associated with the given name.

        The shell object allows to access the low-level shell API.

        :param str shell: Name of the shell.

        :return: The associated shell object.
        :rtype: BaseShell
        """


@add_metaclass(ABCMeta)
class ServicesAPI(object):
    """
    API to gather information and connection parameters to a node services.
    """

    @abstractmethod
    def available_services(self):
        """
        Get the list of all available services.

        :return: The list of all available services.
        :rtype: List of str.
        """

    @abstractmethod
    def get_service(self, service):
        """
        Get the service object associated with the given name.

        The service object holds all connection parameters.

        :param str service: Name of the service.

        :return: The associated service object.
        :rtype: BaseService
        """

    @abstractmethod
    def _register_service(self, name, serviceobj):
        """
        Allow plugin developers to register a service when initializing a node.

        :param str name: Unique name of the service to register.
        :param serviceobj: The service object to register with all connection
         related parameters.
        :type serviceobj: BaseService
        """

    @abstractmethod
    def _get_services_address(self):
        """
        Returns the IP or FQDN of the node so users can connect to the
        registered services.

        .. note::

           This method should be implemented by the platform engine base node.

        :returns: The IP or FQDM of the node.
        :rtype: str
        """


@add_metaclass(ABCMeta)
class StateAPI(object):
    """
    API to control the enable/disabled state of a topology element.
    """

    @abstractmethod
    def is_enabled(self):
        """
        Query if the element is enabled.

        :return: True if the element is enabled, False otherwise.
        :rtype: bool
        """

    @abstractmethod
    def enable(self):
        """
        Enable this element.

        An enabled element allows communication.
        """

    @abstractmethod
    def disable(self):
        """
        Disable this element.

        A disabled element doesn't allow communication.
        """


@add_metaclass(ABCMeta)
class CommonStateAPI(StateAPI):
    """
    Implementation of the StateAPI methods.
    """

    def is_enabled(self):
        """
        Implementation of the ``is_enabled`` interface.

        This method will just return the internal value of the ``_enabled``
        flag.

        See :meth:`StateAPI.is_enabled` for more information.
        """
        return self._enabled

    def enable(self):
        """
        Implementation of the ``enable`` interface.

        This method will just set the value of the ``_enabled`` flag to True.

        See :meth:`StateAPI.enable` for more information.
        """
        self._enabled = True

    def disable(self):
        """
        Implementation of the ``disable`` interface.

        This method will just set the value of the ``_enabled`` flag to False.

        See :meth:`StateAPI.disable` for more information.
        """
        self._enabled = False

__all__ = [
    'HighLevelShellAPI',
    'LowLevelShellAPI',
    'ServicesAPI',
    'StateAPI',
    'CommonStateAPI'
]
