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
Simple switch Topology Docker Node using Ubuntu.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from topology_docker.node import DockerNode
from topology_docker.shell import DockerBashShell


class SwitchNode(DockerNode):
    """
    Simple switch node for the Topology Docker platform engine.

    This base switch loads an ubuntu image (by default) and creates a
    kernel-level bridge where it adds all of its front-panel interfaces to
    emulate the behaviour of a real "dumb" switch.

    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(self, identifier, image='ubuntu:14.04', **kwargs):

        super(SwitchNode, self).__init__(identifier, image=image, **kwargs)

        # Create and register shells
        self._register_shell(
            'bash',
            DockerBashShell(
                self.container_id,
                'bash'
            )
        )
        self._register_shell(
            'bash_front_panel',
            DockerBashShell(
                self.container_id,
                'ip netns exec front_panel bash'
            )
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """
        super(SwitchNode, self).notify_post_build()

        # Let's create the bridge interface and then bring it up
        netns_exec = 'ip netns exec front_panel'
        self._docker_exec(
            '{} ip link add name bridge0 type bridge'.format(netns_exec)
        )
        self._docker_exec(
            '{} ip link set bridge0 up'.format(netns_exec)
        )

        # Get the ports created by the framework
        created_ports = list(self.ports.keys())

        # Add the ports to the bridge (for this they need to be UP first)
        for port in created_ports:
            self._docker_exec('{} ip link set {} up'.format(netns_exec, port))
            self._docker_exec('{} ip link set {} master bridge0'.format(
                netns_exec,
                port
            ))


__all__ = ['SwitchNode']
