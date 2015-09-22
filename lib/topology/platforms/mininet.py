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
Mininet engine platform module for topology.

Topology platform plugin for Mininet.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from six import iterkeys, add_metaclass

from .base import BasePlatform, BaseNode
from ..libraries.manager import libraries


log = logging.getLogger(__name__)


class MininetPlatform(BasePlatform):
    """
    Plugin to build a topology on Mininet.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):
        super(MininetPlatform, self).__init__(timestamp, nmlmanager)
        self._net = None
        self.nmlnode_node_map = {}

    def pre_build(self):
        """
        Brings up a mininet instance.

        Mininet needs a controller to make a topology works.

        See :meth:`BasePlatform.pre_build` for more information.
        """
        from mininet.net import Mininet

        self._net = Mininet()
        self._net.addController(b'c0')

    def add_node(self, node):
        """
        Add new switch or host node.

        See :meth:`BasePlatform.add_node` for more information.
        """
        node_type = node.metadata.get('type', 'switch')
        enode = None

        if node_type == 'switch':
            enode = MininetSwitch(
                self._net.addSwitch(
                    str(node.identifier),
                    dpid=str(len(self.nmlnode_node_map))
                )
            )
        elif node_type == 'host':
            enode = MininetHost(
                self._net.addHost(
                    str(node.identifier),
                    dpid=str(len(self.nmlnode_node_map))
                )
            )
        else:
            raise Exception('Unsupported type {}'.format(node_type))

        self.nmlnode_node_map[node.identifier] = enode
        return enode

    def add_biport(self, node, biport):
        """
        Add port to MininetNode, it is not registered on mininet until a link
        is made.

        See :meth:`BasePlatform.add_biport` for more information.
        FIXME: find a way to create a port on mininet-ovs.
        """
        mn_node = self.nmlnode_node_map[node.identifier]
        port_number = len(mn_node._nmlport_port_map) + 1
        mn_node._nmlport_port_map[biport.identifier] = port_number

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        node_a = self.nmlnode_node_map[nodeport_a[0].identifier]
        port_a = None
        if nodeport_a[1] is not None:
            port_a = node_a._nmlport_port_map[nodeport_a[1].identifier]

        node_b = self.nmlnode_node_map[nodeport_b[0].identifier]
        port_b = None
        if nodeport_b[1] is not None:
            port_b = node_b._nmlport_port_map[nodeport_b[1].identifier]

        self._net.addLink(
            node_a._mininet_node, node_b._mininet_node,
            port1=port_a, port2=port_b
        )

    def post_build(self):
        """
        Starts the mininet platform.

        See :meth:`BasePlatform.post_build` for more information.
        """
        self._net.start()

    def destroy(self):
        """
        Stops the mininet platform.

        See :meth:`BasePlatform.destroy` for more information.
        """
        self._net.stop()


@add_metaclass(ABCMeta)
class MininetNode(BaseNode):
    """
    Mininet Engine Node for Topology.

    This is an adaptator class for between Topology's
    :class:`topology.platforms.base.BaseNode` and Mininet's
    :class:`mininet.node.Node`.

    :param mininet_node: The node as a Mininet object.
    :type mininet_node: :class:`mininet.node.Node`
    """

    @abstractmethod
    def __init__(self, mininet_node, **kwargs):
        super(MininetNode, self).__init__(mininet_node.name, **kwargs)
        self._mininet_node = mininet_node
        self._nmlport_port_map = {}
        self._shells = OrderedDict()
        self._functions = OrderedDict()

        # Add support for communication libraries
        for libname, registry in libraries():
            for register in registry:
                key = '{}_{}'.format(libname, register.__name__)
                self._functions[key] = register

    def send_command(self, command, shell=None):
        """
        Implementation of the ``send_command`` interface.

        See :meth:`topology.platforms.base.BaseNode.send_command` for more
        information.
        """
        if shell is None and self._shells:
            shell = list(iterkeys(self._shells))[0]
        elif shell not in self._shells.keys():
            raise Exception(
                'Shell {} is not supported.'.format(shell)
            )
        return self._shells[shell](command)

    def available_shells(self):
        """
        Implementation of the ``available_shells`` interface.

        See :meth:`topology.platforms.base.BaseNode.available_shells` for more
        information.
        """
        return list(iterkeys(self._shells))

    def send_data(self, data, function=None):
        """
        Implementation of the ``send_data`` interface.

        See :meth:`topology.platforms.base.BaseNode.send_data` for more
        information.
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

        See :meth:`topology.platforms.base.BaseNode.available_functions` for
        more information.
        """
        return list(iterkeys(self._functions))


class MininetSwitch(MininetNode):
    """
    Specilized class for node of type switch.

    See :class:`MininetNode`.
    """

    def __init__(self, mininet_node, **kwargs):
        super(MininetSwitch, self).__init__(mininet_node, **kwargs)
        self._shells['ovs-vsctl'] = self._mininet_node.vsctl
        self._shells['ovs-ofctl'] = self._mininet_node.dpctl
        self._shells['bash'] = self._mininet_node.cmd


class MininetHost(MininetNode):
    """
    Specilized class for node of type host.

    See :class:`MininetNode`.
    """
    def __init__(self, mininet_node, **kwargs):
        super(MininetHost, self).__init__(mininet_node, **kwargs)
        self._shells['bash'] = self._mininet_node.cmd


__all__ = ['MininetPlatform', 'MininetSwitch', 'MininetHost']
