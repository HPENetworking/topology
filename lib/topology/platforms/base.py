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

This module defines the functionality that a topology platform plugin must
provide to be able to create a network using specific hardware.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from datetime import datetime
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from six import add_metaclass, iterkeys

from .shell import ShellContext
from ..libraries.manager import LibsProxy


log = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class BasePlatform(object):
    """
    Base platform engine class.

    This class represent the base interface that topology engines require to
    implement.

    See the :doc:`Plugins Development Guide </plugins>` for reference.

    :param str timestamp: Timestamp in ISO 8601 format.
    :param nmlmanager: Manager holding the NML namespace.
    :type nmlmanager: :class:`pynml.manager.NMLManager`
    """

    @abstractmethod
    def __init__(self, timestamp, nmlmanager):
        pass

    @abstractmethod
    def pre_build(self):
        """
        Preamble hook.

        This hook is called at the first stage of the topology build.
        Use it to setup any requirements your platform has.
        """

    @abstractmethod
    def add_node(self, node):
        """
        Add a node to your platform.

        This method receives a NML node and must return a new Engine Node
        subclass of :class:`BaseNode` that implements the communication
        mechanism with that node.

        :param node: The specification NML node to add to the platform.
        :type node: :class:`pynml.nml.Node`
        :rtype: BaseNode
        :return: Platform specific communication node.
        """

    @abstractmethod
    def add_biport(self, node, biport):
        """
        Add a bidirectional port to the given node.

        This method receives a NML node and a NML bidirectional port that
        specifies the port required to be added. This methods returns nothing
        as the topology users don't expect to deal directly with ports. All
        interaction is done with the nodes.

        :param node: The specification NML node owner of the port.
        :type node: :class:`pynml.nml.Node`
        :param biport: The specification NMP bidirectional port to add to the
         platform.
        :type biport: :class:`pynml.nml.BidirectionalPort`
        :rtype: str
        :return: Real name of the port in the node. This real will be used to
         populate an internal map between the specification name of the port
         and the real name, which can be used to reference the port in commands
         without knowing it's real name in advance.
        """

    @abstractmethod
    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a bidirectional link between given nodes and ports.

        This method receives two tuples with the NML nodes and bidirectional
        ports associated with the bidirectional link and also the NML
        bidirectional link object that specifies the link required to be added
        to the platform. This methods returns nothing as the topology users
        don't expect to deal directly with links. All interaction is done with
        the nodes.

        :param nodeport_a: A tuple (Node, BiPort) of the first endpoint.
        :type nodeport_a:
         (:class:`pynml.nml.Node`, :class:`pynml.nml.BidirectionalPort`)
        :param nodeport_b: A tuple (Node, BiPort) of the second endpoint.
        :type nodeport_b:
         (:class:`pynml.nml.Node`, :class:`pynml.nml.BidirectionalPort`)
        :param bilink: The specification NMP bidirectional link to add to the
         platform.
        :type biport: :class:`pynml.nml.BidirectionalLink`
        """

    @abstractmethod
    def post_build(self):
        """
        Postamble hook.

        This hook is called at the last stage of the topology build.
        Use it to setup any final requirements or start any service before
        using the topology.
        """

    @abstractmethod
    def destroy(self):
        """
        Platform destruction hook.

        Use this to remove all elements from the platform, perform any clean
        and return resources.
        """

    @abstractmethod
    def rollback(self, stage, enodes, exception):
        """
        Platform rollback hook.

        This is called when the build fails, possibly by an exception raised in
        previous hooks.

        :param str stage: The stage the build failed. One of:
         - ``pre_build``.
         - ``add_node``.
         - ``add_biport``.
         - ``add_bilink``.
         - ``post_build``.
        :param enodes: Engine nodes already registered.
        :type enodes: OrderedDict of subclasses of :class:`BaseNode`
        :param Exception exception: The exception caught during build failure.
        """

    @abstractmethod
    def relink(self, link_id):
        """
        Relink back a link specified in the topology.

        :param str link_id: Link identifier to be recreated.
        """

    @abstractmethod
    def unlink(self, link_id):
        """
        Unlink (break) a link specified in the topology.

        :param str link_id: Link identifier to be undone.
        """


@add_metaclass(ABCMeta)
class BaseNode(object):
    """
    Base engine node class.

    This class represent the base interface that engine nodes require to
    implement.

    See the :doc:`Plugins Development Guide </plugins>` for reference.

    :param str identifier: Unique identifier of the engine node.
    :var metadata: Additional metadata (kwargs leftovers).
    """

    @abstractmethod
    def __init__(self, identifier, **kwargs):
        self.identifier = identifier
        self.metadata = kwargs

    @property
    def default_shell(self):
        raise NotImplementedError('default_shell')

    @default_shell.setter
    def default_shell(self, value):
        raise NotImplementedError('default_shell.setter')

    def __call__(self, cmd, shell=None, silent=False):
        return self.send_command(cmd, shell=shell, silent=silent)

    def use_shell(self, shell):
        """
        Create a context manager that allows to use a different default shell
        in a context.

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
        return ShellContext(self, shell)

    @abstractmethod
    def get_shell(self, shell):
        """
        Get the shell object associated with the given name.

        The shell object allows to access the low-level shell API.

        :param str shell: Name of the shell.
        :return: The associated shell object.
        :rtype: :class:`BaseShell`.
        """

    @abstractmethod
    def send_command(self, cmd, shell=None, silent=False):
        """
        Send a command to this engine node.

        :param str cmd: Command to send.
        :param str shell: Shell that must interpret the command.
         `None` for the default shell. Is up to the platform engine to
         determine what the default shell is.
        :param bool silent: If ``False``, print input command and response to
         stdout.
        :rtype: str
        :return: The response of the command.
        """

    @abstractmethod
    def available_shells(self):
        """
        Get the list of available shells.

        :rtype: List of str.
        :return: The list of all available shells. The first one is the
         default (if any).
        """

    @abstractmethod
    def is_enabled(self):
        """
        Query if the device is enabled.

        :rtype: bool
        :return: True if the device is enabled, False otherwise.
        """

    @abstractmethod
    def enable(self):
        """
        Enable this device.

        An enabled device allows communication with.
        """

    @abstractmethod
    def disable(self):
        """
        Disable this device.

        A disabled device doesn't allow communication with.
        """


@add_metaclass(ABCMeta)
class CommonNode(BaseNode):
    """
    Base engine node class with a common base implementation.

    This class provides a basic common implementation for managing shells and
    functions, where an internal ordered dictionary handles the keys for
    functions that implements the logic for those shells or functions.

    Child classes will then only require to populate the internal dictionaries
    with those handling functions to delegate the process of the call.

    In particular, this class implements support for topology communication
    libraries and will ad-hoc to the internal functions dictionary all
    libraries available.

    See :class:`BaseNode`.
    """

    @abstractmethod
    def __init__(self, identifier, **kwargs):
        super(CommonNode, self).__init__(identifier, **kwargs)
        self._shells = OrderedDict()
        self._enabled = True
        self._default_shell = None

        # Add support for communication libraries
        self.libs = LibsProxy(self)

    @property
    def default_shell(self):
        return self._default_shell

    @default_shell.setter
    def default_shell(self, value):
        if value not in self._shells:
            raise Exception(
                'Cannot set default shell. Unknown shell "{}"'.format(value)
            )
        self._default_shell = value

    def get_shell(self, shell):
        """
        Implementation of the ``get_shell`` interface.

        This method will return the shell object associated with the given
        shell name.

        See :meth:`BaseNode.get_shell` for more information.
        """
        if shell not in self._shells:
            raise Exception(
                'Unknown shell "{}"'.format(shell)
            )
        return self._shells[shell]

    def send_command(self, cmd, shell=None, silent=False):
        """
        Implementation of the ``send_command`` interface.

        This method will lookup for the shell argument in an internal ordered
        dictionary to fetch a function to delegate the command to. If None is
        provided, the first key of the dictionary will be used.

        See :meth:`BaseNode.send_command` for more information.
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

        if not silent:
            print('{} [{}].send_command(\'{}\', shell=\'{}\') ::'.format(
                datetime.now().isoformat(), self.identifier, cmd, shell
            ))

        response = self._shells[shell](cmd)

        if not silent:
            print(response)

        return response

    def available_shells(self):
        """
        Implementation of the ``available_shells`` interface.

        This method will just list the available keys in the internal ordered
        dictionary.

        See :meth:`BaseNode.available_shells` for more information.
        """
        return list(iterkeys(self._shells))

    def is_enabled(self):
        """
        Implementation of the ``is_enabled`` interface.

        This method will just return the internal value of the ``_enabled``
        flag.

        See :meth:`BaseNode.is_enabled` for more information.
        """
        return self._enabled

    def enable(self):
        """
        Implementation of the ``enable`` interface.

        This method will just set the value of the ``_enabled`` flag to True.

        See :meth:`BaseNode.enable` for more information.
        """
        self._enabled = True

    def disable(self):
        """
        Implementation of the ``disable`` interface.

        This method will just set the value of the ``_enabled`` flag to False.

        See :meth:`BaseNode.disable` for more information.
        """
        self._enabled = False


__all__ = ['BasePlatform', 'BaseNode', 'CommonNode']
