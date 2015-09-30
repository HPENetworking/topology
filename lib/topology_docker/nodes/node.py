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
topology_docker base node module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from docker import Client

from topology.platforms.base import CommonNode

from ..shell import DockerShell
from ..platform import iface_name


class DockerNode(CommonNode):
    """
    An instance of this class will create a detached Docker container.

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node.
    :param str command: The command to run when the container is brought up.
    """

    def __init__(
            self, identifier,
            image='ubuntu', command='bash', binds=None, **kwargs):

        super(DockerNode, self).__init__(identifier, **kwargs)

        self._pid = None
        self._image = image
        self._command = command
        self._client = Client()

        self._host_config = self._client.create_host_config(
            # Container is given access to all devices
            privileged=True,
            # Avoid connecting to host bridge, usually docker0
            network_mode='none',
            binds=binds
        )

        self._container_id = self._client.create_container(
            image=self._image,
            command=self._command,
            name=identifier,
            detach=True,
            tty=True,
            host_config=self._host_config
        )['Id']

        self._shells['bash'] = DockerShell(self.identifier, 'bash', '.*#')
        self._ports = {}

    def notify_add_biport(self, node, biport):
        """
        FIXME: Document.
        """
        iface = iface_name(node, biport)
        self._ports[biport.identifier] = {
            'iface': iface,
            'created': False,
            'port_number': biport.metadata.get('port_number', None)
        }

    def notify_add_bilink(self, nodeport, bilink):
        """
        FIXME: Document.
        """
        node, biport = nodeport
        self._ports[biport.identifier]['created'] = True

    def notify_post_build(self):
        """
        FIXME: Document.
        """
        cmd_tpl = 'ip tuntap add dev {iface} mode tap'

        for port_spec in self._ports.values():
            if not port_spec['created']:
                self.send_command(
                    cmd_tpl.format(iface=port_spec['iface']),
                    shell='bash'
                )

    def start(self):
        """
        Start the docker node and configures a netns for it.
        """
        self._client.start(self._container_id)
        self._pid = self._client.inspect_container(
            self._container_id)['State']['Pid']

    def stop(self):
        """
        Stop docker container and remove its netns
        """
        self._client.stop(self._container_id)
        self._client.wait(self._container_id)
        self._client.remove_container(self._container_id)


__all__ = ['DockerNode']
