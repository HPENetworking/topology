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
This module extends from mininet Node class with Docker support.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging

from docker import Client

from subprocess import check_call
from shlex import split as shplit

from topology.platforms.base import BasePlatform, CommonNode

log = logging.getLogger(__name__)


class DockerPlatform(BasePlatform):
    """
    Plugin to build a topology on Mininet.

    See :class:`topology.platforms.base.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):
        self.nmlnode_node_map = {}

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """

    def add_node(self, node):
        """
        Add new switch or host node.

        See :meth:`BasePlatform.add_node` for more information.
        """
        node_type = node.metadata.get('type', 'switch')
        image = node.metadata.get('image', 'ubuntu')

        enode = None

        if node_type == 'switch':
            enode = DockerSwitch(str(node.identifier), image=image)
        elif node_type == 'host':
            enode = DockerHost(str(node.identifier), image=image)
        else:
            raise Exception('Unsupported type {}'.format(node_type))

        # FIXME: consider moving start to post_build
        enode.start()

        self.nmlnode_node_map[node.identifier] = enode
        return enode

    def add_biport(self, node, biport):
        """
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
        netns_a = self.nmlnode_node_map[
            nodeport_a[0].identifier].name
        netns_b = self.nmlnode_node_map[
            nodeport_b[0].identifier].name

        intf_a = nodeport_a[1].identifier
        intf_b = nodeport_b[1].identifier

        # Check docs.docker.com/articles/networking/#building-a-point-to-point-connection # noqa
        command_template = """ \
            ip link add {intf_a} type veth peer name {intf_b}
            ip link set {intf_a} netns {netns_a}
            ip link set {intf_b} netns {netns_b} \
            """
        commands = command_template.format(**locals())

        for command in commands.splitlines():
            check_call(shplit(command.lstrip()))

    def post_build(self):
        """
        Starts the mininet platform.

        See :meth:`BasePlatform.post_build` for more information.
        """

    def destroy(self):
        """
        Stops the mininet platform.

        See :meth:`BasePlatform.destroy` for more information.
        """
        for enode in self.nmlnode_node_map.values():
            enode.stop()


class DockerNode(CommonNode):

    """
    An instance of this class will create a detached Docker container.

    :param str name: The name of the node.
    :param str image: The image to run on this node.
    :param str command: The command to run when the container is brought up.
    """

    def __init__(self, name, image='ubuntu', command='bash', **kwargs):
        if name is None:
            name = str(id(self))

        self.name = name
        self._image = image
        self._command = command
        self._client = Client()
        self._container_id = self._client.create_container(
            image=self._image,
            command=self._command,
            name=name,
            detach=True,
            tty=True,
            host_config=self._client.create_host_config(
                privileged=True,     # Container is given access to all devices
                network_mode='none'  # Avoid connecting to host bridge,
                                     # usually docker0

            )
        )['Id']

        super(DockerNode, self).__init__(name, **kwargs)

    def _create_netns(self):
        """
        Docker creates a netns. This method makes that netns avaible
        to the host
        """
        pid = self._client.inspect_container(
            self._container_id)['State']['Pid']
        name = self.name

        command_template = """ \
            mkdir -p /var/run/netns
            ln -s /proc/{pid}/ns/net /var/run/netns/{name} \
            """
        commands = command_template.format(**locals())

        for command in commands.splitlines():
            check_call(shplit(command.lstrip()))

    def start(self):
        self._client.start(self._container_id)
        self._create_netns()

    def stop(self):
        self._client.stop(self._container_id)
        self._client.wait(self._container_id)
        self._client.remove_container(self._container_id)

        # remove netns
        command_template = "ip netns del {self.name}"
        command = command_template.format(**locals())
        check_call(shplit(command))


class DockerSwitch(DockerNode):
    pass


class DockerHost(DockerNode):
    pass


__all__ = ['DockerHost', 'DockerSwitch']
