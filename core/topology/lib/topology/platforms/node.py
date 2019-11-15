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
Base platform engine module for topology.

This module defines the functionality that a Topology Engine Node must
implement to be able to create a network using a specific environment.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from datetime import datetime
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from six import add_metaclass, iterkeys

from .service import BaseService
from ..libraries.manager import LibsProxy
from .shell import ShellContext, BaseShell


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
        :param bool silent: True to call the shell logger, False
         otherwise.

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
    API to control the enable/disabled state of a node.
    """

    @abstractmethod
    def is_enabled(self):
        """
        Query if the node is enabled.

        :return: True if the node is enabled, False otherwise.
        :rtype: bool
        """

    @abstractmethod
    def enable(self):
        """
        Enable this node.

        An enabled node allows communication.
        """

    @abstractmethod
    def disable(self):
        """
        Disable this node.

        A disabled node doesn't allow communication.
        """


@add_metaclass(ABCMeta)
class BaseNode(HighLevelShellAPI, LowLevelShellAPI, ServicesAPI, StateAPI):
    """
    Base engine node class.

    This class represent the base interface that engine nodes require to
    implement.

    See the :doc:`Plugins Development Guide </plugins>` for reference.

    :param str identifier: User identifier of the engine node.

    :var identifier: User identifier of the engine node. Please note that
     this identifier is unique in the topology being built, but is not unique
     in the execution system.
    :var metadata: Additional metadata (kwargs leftovers).
    :var ports: Mapping between node ports and engine ports. This variable
     is populated by the :class:`topology.manager.TopologyManager`.
    """

    @abstractmethod
    def __init__(self, identifier, **kwargs):
        super(BaseNode, self).__init__()
        self.identifier = identifier
        self.metadata = kwargs
        self.ports = OrderedDict()


@add_metaclass(ABCMeta)
class CommonNode(BaseNode):
    """
    Base engine node class with a common base implementation.

    This class provides a basic common implementation for managing shells and
    services. Internal ordered dictionaries handles the keys for
    shells and services objects that implements the logic for those shells or
    services.

    Child classes will then only require to call registration methods
    :meth:`_register_shell` and :meth:`_register_service`.

    In particular, this class implements support for Communication Libraries
    using class :class:`LibsProxy` that will hook with all available libraries.

    See :class:`BaseNode`.

    .. note::

       The method :meth: ``_get_services_address`` should be provided by the
       Platform Engine base node.
    """

    @abstractmethod
    def __init__(self, identifier, **kwargs):
        super(CommonNode, self).__init__(identifier, **kwargs)

        # Shell(s) API
        self._default_shell = None
        self._shells = OrderedDict()

        # Services API
        self._services = OrderedDict()

        # State API
        self._enabled = True

        # Communication Libraries support
        self.libs = LibsProxy(self)

    # HighLevelShellAPI

    @property
    def default_shell(self):
        return self._default_shell

    @default_shell.setter
    def default_shell(self, value):
        if value not in self._shells:
            raise KeyError(
                'Cannot set default shell. Unknown shell "{}"'.format(value)
            )
        self._default_shell = value

    def available_shells(self):
        """
        Implementation of the public ``available_shells`` interface.

        This method will just list the available keys in the internal ordered
        dictionary.

        See :meth:`HighLevelShellAPI.available_shells` for more information.
        """
        return list(iterkeys(self._shells))

    def send_command(self, cmd, shell=None, silent=False):
        """
        Implementation of the public ``send_command`` interface.

        This method will lookup for the shell argument in an internal ordered
        dictionary to fetch a shell object to delegate the command to.
        If None is provided, the default shell of the node will be used.

        See :meth:`HighLevelShellAPI.send_command` for more information.
        """

        # Check at least one shell is available
        if not self._shells:
            raise Exception(
                'Node {} doens\'t have any shell.'.format(self.identifier)
            )

        # Check if default shell is already set
        if self._default_shell is None:
            self._default_shell = list(iterkeys(self._shells))[0]

        # Check requested shell is supported
        if shell is None:
            shell = self._default_shell
        elif shell not in self._shells.keys():
            raise Exception(
                'Shell {} is not supported.'.format(shell)
            )

        active_shell = self.get_shell(shell)

        active_shell.send_command(cmd, silent=silent)

        response = active_shell.get_response(silent=silent)

        return response

    def _register_shell(self, name, shellobj):
        """
        Implementation of the private ``_register_shell`` interface.

        This method will lookup for the shell name argument in an internal
        ordered dictionary and, if inexistent, it will register the given
        shell object.

        See :meth:`HighLevelShellAPI._register_shell` for more information.
        """
        assert isinstance(shellobj, BaseShell)

        if name in self._shells:
            raise KeyError('Shell "{}" already registered'.format(name))
        if not name:
            raise KeyError('Invalid name for shell "{}"'.format(name))

        self._shells[name] = shellobj

        # Add the node identifier and the shell name to the shell object to
        # enable logging in the shell object itself
        shellobj._register_node(self.identifier, name)

    # LowLevelShellAPI

    def get_shell(self, shell):
        """
        Implementation of the public ``get_shell`` interface.

        This method will return the shell object associated with the given
        shell name.

        See :meth:`LowLevelShellAPI.get_shell` for more information.
        """
        if shell not in self._shells:
            raise KeyError(
                'Unknown shell "{}"'.format(shell)
            )
        return self._shells[shell]

    def use_shell(self, shell):
        """
        Implementation of the public ``use_shell`` interface.

        This method allows to create contexts (using a Python Context Manager)
        that allows the user, by the means of a ``with`` statement, to create
        a context to use a specific shell in it.

        See :meth:`LowLevelShellAPI.use_shell` for more information.
        """
        return ShellContext(self, shell)

    # ServicesAPI

    def available_services(self):
        """
        Implementation of the public ``available_services`` interface.

        This method will just list the available keys in the internal ordered
        dictionary.

        See :meth:`ServicesAPI.available_services` for more information.
        """
        return list(iterkeys(self._services))

    def get_service(self, service):
        """
        Implementation of the public ``get_service`` interface.

        This method will return the service object associated with the given
        service name.

        See :meth:`ServicesAPI.get_service` for more information.
        """
        if service not in self._services:
            raise KeyError(
                'Unknown service "{}"'.format(service)
            )

        # Set the node address
        serviceobj = self._services[service]
        serviceobj.address = self._get_services_address()

        return serviceobj

    def _register_service(self, name, serviceobj):
        """
        Implementation of the private ``_register_service`` interface.

        This method will lookup for the service name argument in an internal
        ordered dictionary and, if inexistent, it will register the given
        service object.

        See :meth:`ServicesAPI._register_service` for more information.
        """
        assert isinstance(serviceobj, BaseService)

        if name in self._services:
            raise KeyError('Service "{}" already registered'.format(name))
        if not name:
            raise KeyError('Invalid name for service "{}"'.format(name))

        self._services[name] = serviceobj

    # StateAPI

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

    def _log_command(self, command, shell):
        """
        Command logging function for low-level shell API usage.

        :param str command: Sent command to be logged.
        :param str shell: Name of the shell that sends the command.
        """

        print(
            '{} [{}].send_command(\'{}\', shell=\'{}\') ::'.format(
                datetime.now().isoformat(), self.identifier, command, shell
            )
        )

    def _log_response(self, response, shell):
        """
        Response logging function for low-level shell API usage.

        :param str response: Command response to be logged.
        :param str shell: Name of the shell that receives the command response.
        """
        print(response.encode(self._shells[shell]._encoding))

    def _set_test_log(self, log):
        """
        Set the current test execution log. This log is set by test requiest

        :param log: the logging object requested
        """
        for shell in self._shells:
            self.get_shell(shell)._testlog = log


__all__ = [
    'HighLevelShellAPI',
    'LowLevelShellAPI',
    'ServicesAPI',
    'StateAPI',
    'BaseNode',
    'CommonNode'
]
