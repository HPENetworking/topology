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
Custom Topology Docker Node for Toxin.

"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell


class ToxinNode(DockerNode):
    """
    Custom engine node for the Topology docker platform engine.

    This custom node loads an OpenvSwitch image and has busybox as console.

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node.
    :param str command: The command to run when the container is brought up.
    :param list binds: A list of directories endpoints to bind in container in
     the form:

     ::

        [
            '/tmp:/tmp',
            '/dev/log:/dev/log',
            '/sys/fs/cgroup:/sys/fs/cgroup'
        ]
    """

    def __init__(
            self, identifier,
            image='toxin:latest',
            command='sh', binds=None,
            **kwargs):

        # Add binded directories
        if binds is None:
            binds = []

        super(ToxinNode, self).__init__(
            identifier, image=image, command=command, binds=binds, **kwargs
        )

        # Add bash shell
        self._shells['bash'] = DockerShell(
            self.container_id, 'bash', 'root@.*/#'
        )
        self._shells['txn-shell'] = DockerShell(
            self.container_id, 'txn-shell', '>>>'
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        super(ToxinNode, self).notify_post_build()

        for portlbl in self.ports:
            self.port_state(portlbl, True)

        from subprocess import Popen
        from shlex import split as shsplit
        Popen(shsplit(
            'docker exec {} txnd'.format(
                self.container_id
            )
        ))

__all__ = ['ToxinNode']
