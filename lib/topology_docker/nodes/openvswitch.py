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
Custom Topology Docker Node for OpenvSwitch.

    http://openvswitch.org/

Check https://hub.docker.com/r/socketplane/openvswitch/ for docker container.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from time import sleep
from subprocess import Popen, check_output
from shlex import split as shsplit

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell


class OpenvSwitchNode(DockerNode):
    """
    Custom Open vSwitch node for the Topology Docker platform engine.

    This custom node loads and starts an Open vSwitch image. It uses the OVS
    docker image. based on busybox OVS. It can be configured using
    ``ovs-vsctl``, ``ovs-ofctl`` and ``ovs-appclt`` through the default
    shell (sh). Interfaces are not auto-started by the node.

    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(
            self, identifier,
            image='topology/openvswitch:latest',
            **kwargs):

        # Supervisor daemon
        self._supervisord = None

        # Check if openvswitch Kernel module is loaded
        res = check_output('lsmod').decode('utf-8')
        if 'openvswitch' not in res:
            raise RuntimeError(
                'Open vSwitch kernel module not loaded.'
            )

        super(OpenvSwitchNode, self).__init__(
            identifier, image=image, command='sh', **kwargs
        )

        # Add bash shell
        self._shells['sh'] = DockerShell(
            self.container_id, 'sh', '/ .*#'
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        super(OpenvSwitchNode, self).notify_post_build()

        # FIXME: this is a workaround
        self._docker_exec(
            "sed -i -e 's/port = 9001/port = 127.0.0.1:9001/g' "
            "-e 's/nodaemon=true/nodaemon=false/g' "
            "/etc/supervisord.conf"
        )

        self._supervisord = Popen(shsplit(
            'docker exec {} supervisord'.format(self.container_id)
        ))

        # Wait for the configure-ovs script to exit by polling supervisorctl
        config_timeout = 100
        i = 0
        while i < config_timeout:
            config_status = self._docker_exec(
                'supervisorctl status configure-ovs'
            )

            if 'EXITED' not in config_status:
                sleep(0.1)
            else:
                break
            i += 1

        if i == config_timeout:
            raise RuntimeError('configure-ovs did not exit!')


__all__ = ['OpenvSwitchNode']
