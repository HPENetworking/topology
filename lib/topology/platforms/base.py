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
Base engine platform module for topology.

This module defines the functionality that a topology platform plugin must
provide to be able to create a network using specific hardware.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from six import add_metaclass, iterkeys

from ..libraries.manager import libraries


log = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class BasePlatform(object):
    """
    Base engine platform class.

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
        pass

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
        pass

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
        """
        pass

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
        pass

    @abstractmethod
    def post_build(self):
        """
        Postamble hook.

        This hook is called at the last stage of the topology build.
        Use it to setup any final requirements or start any service before
        using the topology.
        """
        pass

    @abstractmethod
    def destroy(self):
        """
        Platform destruction hook.

        Use this to remove all elements from the platform, perform any clean
        and return resources.
        """
        pass

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
        pass


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

    def __call__(self, cmd, shell=None, silent=False):
        return self.send_command(cmd, shell=shell, silent=silent)

    @abstractmethod
    def send_command(self, cmd, shell=None, silent=False):
        """
        Send a command to this engine node.

        :param str cmd: Command to send.
        :param str shell: Shell that must interpret the command.
         `None` for the default shell. Is up to the engine platform to
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
    def send_data(self, data, function=None):
        """
        Send data to a function and return it's result.

        This interface is particularly useful to implement communication with
        this node when the node has a Restful API or other programmatic
        interface. Another option is to provide wrapper functions to
        known CLI commands while implementing parser for their outputs.

        :param dict data: Data to send.
        :param str function: The name of the function to call with data.
         `None` is the default function.Is up to the engine platform to
         determine what the default function is.
        :rtype: dict
        :return: The response of the function.
        """

    @abstractmethod
    def available_functions(self):
        """
        Get the list of available functions.

        :rtype: List of str.
        :return: The list of all available functions. The first one is the
         default (if any).
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
        self._functions = OrderedDict()

        # Add support for communication libraries
        for libname, registry in libraries():
            for register in registry:
                key = '{}_{}'.format(libname, register.__name__)
                self._functions[key] = register

    def send_command(self, cmd, shell=None, silent=False):
        """
        Implementation of the ``send_command`` interface.

        This method will lookup for the shell argument in an internal ordered
        dictionary to fetch a function to delegate the command to. If None is
        provided, the first key of the dictionary will be used.

        See :meth:`BaseNode.send_command` for more information.
        """
        if shell is None and self._shells:
            shell = list(iterkeys(self._shells))[0]
        elif shell not in self._shells.keys():
            raise Exception(
                'Shell {} is not supported.'.format(shell)
            )

        response = self._shells[shell](cmd)

        if not silent:
            print('[{}].send_command({}) ::'.format(self.identifier, cmd))
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

    def send_data(self, data, function=None):
        """
        Implementation of the ``send_data`` interface.

        This method will lookup for the function argument in an internal
        ordered dictionary to fetch a function to delegate the command to.
        If None is  provided, the first key of the dictionary will be used.

        Note that this internal dictionary is populated at instantiation of the
        node using the :func:`topology.libraries.manager.libraries` function.

        See :meth:`BaseNode.send_data` for more information.
        """
        if function is None and self._functions:
            function = list(iterkeys(self._functions))[0]
        elif function not in self._functions.keys():
            raise Exception(
                'Function {} is not supported.'.format(function)
            )
        return self._functions[function](data)

    def available_functions(self):
        """
        Implementation of the ``available_functions`` interface.

        This method will just list the available keys in the internal ordered
        dictionary.

        See :meth:`BaseNode.available_functions` for more information.
        """
        return list(iterkeys(self._functions))


__all__ = ['BasePlatform', 'BaseNode', 'CommonNode']
