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
Custom Topology Docker Node for Toxin.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from subprocess import Popen
from shlex import split as shsplit

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell


class ToxinNode(DockerNode):
    """
    Custom Toxin packet generator node for the Topology Docker platform engine.

    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(
            self, identifier,
            image='hpe-networking/toxin:latest',
            registry='docker.hos.hpecorp.net',
            **kwargs):

        super(ToxinNode, self).__init__(
            identifier, image=image, registry=registry, network_mode='bridge',
            **kwargs
        )

        # Add txn shell (default shell)
        # FIXME: Change to txn when migrated to Toxin 2.0
        self._shells['txn-shell'] = DockerShell(
            self.container_id, 'txn-shell', '>>>'
        )

        # Add bash shell
        self._shells['bash'] = DockerShell(
            self.container_id, 'sh -c "TERM=dumb bash"', 'root@.*:.*# '
        )

        # Toxin daemon process
        self._txnd = None

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        super(ToxinNode, self).notify_post_build()

        # Bring up all interfaces
        for portlbl in self.ports:
            self.set_port_state(portlbl, True)

        # Get bridge information
        docker0 = self._client.inspect_container(
            self.container_id
        )['NetworkSettings']['Gateway']
        docker0_list = docker0.split('.')
        obm_subnet = '{}.{}.0.0'.format(docker0_list[0], docker0_list[1])

        # Firewall bridge interface to host, to avoid routing through it
        commands = [
            'route del default',
            'route add -net {} netmask 255.255.0.0 reject'.format(obm_subnet),
            'route add -net {} netmask 255.255.255.255 dev eth0'.format(
                docker0
            )
        ]

        for command in commands:
            self._docker_exec(command)

        # Start Toxin daemon
        # FIXME: Write configuration file or specify interfaces to hook
        self._txnd = Popen(shsplit(
            'docker exec {} txnd'.format(self.container_id)
        ))


__all__ = ['ToxinNode']
