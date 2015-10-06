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
Custom Topology Docker Node for OpenvSwitch.

    http://openvswitch.org/

Check https://hub.docker.com/r/socketplane/openvswitch/ for docker container.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell


class OpenvSwitchNode(DockerNode):
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
            image='socketplane/openvswitch:latest',
            command='sh', binds=None,
            **kwargs):

        # Add binded directories
        if binds is None:
            binds = []

        super(OpenvSwitchNode, self).__init__(
            identifier, image=image, command=command, binds=binds, **kwargs
        )

        # Add bash shell
        self._shells['sh'] = DockerShell(
            self.identifier, 'sh', '/ .*#'
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        super(OpenvSwitchNode, self).notify_post_build()

    def start(self):
        """
        Start the docker node.
        """
        super(OpenvSwitchNode, self).start()

        # FIXME: this is a workaround
        self("sed -i -e 's/port = 9001/port = 127.0.0.1:9001/g' "
             "-e 's/nodaemon=true/nodaemon=false/g' "
             "/etc/supervisord.conf")
        self('supervisord')

__all__ = ['OpenvSwitchNode']
