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
from shlex import split as shsplit
from subprocess import check_call, Popen

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell
from topology_docker.utils import ensure_dir


class P4SwitchNode(DockerNode):
    """
    Barefoot's P4 switch node. Runs a configurable beavioral simulator.

    This custom node loads a P4 switch docker image built from the
    p4factory repository. The switch is configurable through switch-specific
    interfaces and the standard SAI interface (incomplete).

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node. The image can also be
     setup using the environment variable ``P4SWITCH_IMAGE``. If present, it
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
            type='p4switch',
            image='hpe-networking/p4dockerswitch:latest',
            registry='docker.hos.hpecorp.net',
            binds=None):

        # Fetch image from environment but only if default image is being used
        if image == 'hpe-networking/p4dockerswitch:latest':
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
            identifier, image=image, registry=registry,
            command='/bin/bash', binds=binds
        )

        # Behavioral model daemon process
        self._bm_daemon = None

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

        # Add bash shell
        self._shells['bash'] = DockerShell(
            self.container_id, 'sh -c "TERM=dumb bash"', 'root@.*:.*# '
        )

        # Add SAI shell (https://github.com/p4lang/switchsai)
        self._shells['sai'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb bash"',
            'root@.*:.*# ',
            '/p4factory/targets/switch/tests/pd_thrift/switch_sai_rpc-remote '
            '-h localhost:9092 '
        )

        # Add switchapi shell (https://github.com/p4lang/switchapi)
        self._shells['api'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb bash"',
            'root@.*:.*# ',
            '/p4factory/targets/switch/tests/pd_thrift/switch_api_rpc-remote '
            '-h localhost:9091 '
        )

        # Add PD shells
        self._shells['pd_conn_mgr'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb bash"',
            'root@.*:.*# ',
            '/p4factory/targets/switch/tests/pd_thrift/conn_mgr-remote '
            '-h localhost:9090 '
        )
        self._shells['pd_mc'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb bash"',
            'root@.*:.*# ',
            '/p4factory/targets/switch/tests/pd_thrift/mc-remote '
            '-h localhost:9090 '
        )
        self._shells['pd_p4'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb bash"',
            'root@.*:.*# ',
            '/p4factory/targets/switch/tests/pd_thrift/dc-remote '
            '-h localhost:9090 '
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

        if self.metadata.get('autostart', True):

            check_call(shsplit(
                'docker exec {} '
                'ip link add name veth250 type veth peer name veth251'
                .format(
                    self.container_id)
            ))
            check_call(shsplit(
                'docker exec {} ip link set dev veth250 up'.format(
                    self.container_id)
            ))
            check_call(shsplit(
                'docker exec {} ip link set dev veth251 up'.format(
                    self.container_id)
            ))

            # Bring up all interfaces
            # FIXME: attach only interfaces brought up by the user
            for portlbl in self.ports:
                self.set_port_state(portlbl, True)

            args = [
                '/p4factory/targets/switch/behavioral-model',
                '--no-veth',
                '--no-pcap'
            ]

            # set openflow controller IP if necessary
            if self.metadata.get('ofip', None) is not None:
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
            self._bm_daemon = Popen(shsplit(
                'docker exec {} '.format(self.container_id) + ' '.join(args)
            ))


__all__ = ['P4SwitchNode']
