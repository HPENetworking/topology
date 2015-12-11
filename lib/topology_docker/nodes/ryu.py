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
Custom Topology Docker Node for OpenSwitch.

    http://openswitch.net/
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from shutil import copy
from os import environ, path
from time import sleep
from shlex import split as shsplit
from subprocess import check_output, Popen

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell
from topology_docker.utils import ensure_dir


class RyuControllerNode(DockerNode):
    """
    Custom Ryu SDN controller node capable of running custom apps.

    This custom node loads a Ryu docker image. It takes and runs a custom
    app by using ryu-manager.

    The default image is osrg/ryu from:
    - https://hub.docker.com/r/osrg/ryu/
    - https://github.com/osrg/dockerfiles/blob/master/ryu/Dockerfile

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node. The image can also be
     setup using the environment variable ``RYU_IMAGE``. If present, it
     will take precedence to this argument in runtime.
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
            type='ryu',
            image='topology_ryu:latest', binds=None):

        # Fetch image from environment but only if default image is being used
        if image == 'topology_ryu:latest':
            image = environ.get('RYU_IMAGE', image)

        # Determine shared directory
        shared_dir = '/tmp/topology_{}_{}'.format(identifier, str(id(self)))
        ensure_dir(shared_dir)

        # Add binded directories
        if binds is None:
            binds = []
        binds.extend([
            '{}:/tmp'.format(shared_dir)
        ])

        super(RyuControllerNode, self).__init__(
            identifier, image=image, command='/bin/bash', binds=binds
        )

        # Supervisor daemon
        self._supervisord = None

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

        # Copy the ryu app into the container
        self.app_name = self.metadata.get('app', None)
        if self.app_name is not None:
            copy(self.app_name, self.shared_dir)

        # Add bash shell
        self._shells['bash'] = DockerShell(
            self.container_id, 'sh -c "TERM=dumb bash"', 'root@.*:.*# '
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """

        super(RyuControllerNode, self).notify_post_build()
        self._setup_system()

    def _setup_system(self):
        """
        Setup the controller image for testing.

        #. Bring up the ports connecting to the datapaths
        #. Run ryu-manager
        """

        # Ryu should be started by Topology
        if self.metadata.get('autostart', True):

            # Get the app file (or default)
            if self.app_name is not None:
                app_path = '/tmp/' + path.basename(self.app_name)
            else:
                app_path = '/root/ryu-master/ryu/app/simple_switch.py'

            # run ryu app using ryu-manager
            self._supervisord = Popen(shsplit(
                'docker exec {} '
                'sh -c "RYU_COMMAND=\'/root/ryu-master/bin/ryu-manager {} '
                '--verbose\' supervisord"'.format(
                    self.container_id,
                    app_path)
            ))

            # Wait for ryu-manager to start
            config_timeout = 100
            i = 0
            while i < config_timeout:
                config_status = check_output(shsplit(
                    'docker exec {} supervisorctl status ryu-manager'.format(
                        self.container_id)
                ), universal_newlines=True)

                if 'RUNNING' not in config_status:
                    sleep(0.1)
                else:
                    break
                i += 1

            if i == config_timeout:
                raise RuntimeError(
                    'ryu-manager did not reach RUNNING state on supervisor!'
                )


__all__ = ['RyuControllerNode']
