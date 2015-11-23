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
Custom P4 Switch Topology Docker Node.

    http://openswitch.net/
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import environ

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell
from topology_docker.utils import ensure_dir


class P4SwitchNode(DockerNode):
    """
    Custom engine node for the Topology docker platform engine.

    This custom node loads a P4 switch docker image with bash as default
    console.

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node. The image can also be
     setup using the environment variable ``P4SWITCH_IMAGE``. If present, it
     will take precedence to this argument in runtime.
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
            image='p4dockerswitch:latest', command='/bin/bash', binds=None,
            **kwargs):

        # Fetch image from environment but only if default image is being used
        if image == 'p4dockerswitch:latest':
            image = environ.get('P4SWITCH_IMAGE', image)

        # Determine shared directory
        shared_dir = '/tmp/topology_{}_{}'.format(identifier, str(id(self)))
        ensure_dir(shared_dir)

        # Add binded directories
        if binds is None:
            binds = []
        binds.extend([
            '{}:/tmp'.format(shared_dir)
        ])

        super(P4SwitchNode, self).__init__(
            identifier, image=image, command=command, binds=binds, **kwargs
        )

        # Get ip of SDN controller
        self._ofip = kwargs.get('ofip', None)

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

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

        super(P4SwitchNode, self).notify_post_build()
        self._setup_system()

    def _setup_system(self):
        """
        Setup the P4 image for testing.

        #. Create the CPU virtual eth pair used by the P4 switch
        #. Bring up the interfaces required to run the switch
        #. Run the switch program
        """

        self(
            'ip link add name veth250 type veth peer name veth251',
            shell='bash'
        )
        self('ip link set dev veth250 up', shell='bash')
        self('ip link set dev veth251 up', shell='bash')

        # Bring up interfaces
        for portlbl in self.ports:
            self.port_state(portlbl, True)

        args = [
            '/p4factory/targets/switch/behavioral-model',
            '--pd-server',
            '127.0.0.1:22000',
            '--no-veth',
            '--no-pcap'
        ]

        # set openflow controller IP if necessary
        if self._ofip is not None:
            args.extend(['--of-ip', self._ofip])

        # ifaces are ready in post_build
        # start the switch program with options:
        #  -i 1 -i 2 -i 3 -i 4 ...
        for iface in self.ports.values():
            args.extend(['-i', iface])

        # redirect stdout & stderr to log file
        # run in background
        args.extend(['&>/tmp/switch.log', '&'])

        # run command
        # TODO: check for posible error code
        self(' '.join(args))


__all__ = ['P4SwitchNode']
