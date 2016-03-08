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
Custom P4 Switch Topology Docker Node.

    http://p4.org/p4/an-open-source-p4-switch-with-sai-support/
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from subprocess import Popen
from shlex import split as shsplit

from topology_docker.node import DockerNode
from topology_docker.utils import ensure_dir
from topology_docker.shell import DockerBashShell


class P4SwitchNode(DockerNode):
    """
    Custom Barefoot P4 node for the Topology Docker platform engine.

    This custom node loads a P4 switch docker image built from the
    p4factory repository. The switch is configurable through switch-specific
    interfaces and the standard SAI interface (incomplete).

    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(
            self, identifier,
            image='topology/p4switch:latest', binds=None,
            **kwargs):

        # Determine shared directory
        shared_dir = '/tmp/topology_{}_{}'.format(identifier, str(id(self)))
        ensure_dir(shared_dir)

        # Add binded directories
        container_binds = [
            '{}:/tmp'.format(shared_dir)
        ]
        if binds is not None:
            container_binds.append(binds)

        super(P4SwitchNode, self).__init__(
            identifier,
            image=image, binds=';'.join(container_binds),
            **kwargs
        )

        # Behavioral model daemon process
        self._bm_daemon = None

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

        # Add bash shell
        self._shells['bash'] = DockerBashShell(
            self.container_id, 'bash'
        )

        # NOTE: It seems that nobody is using this shells.
        # They got commented when migrating to the new Shell API as not enough
        # knowledge was gathered to determine how to migrate them.

        # Add SAI shell
        # https://github.com/p4lang/switch/tree/master/switchsai
        # self._shells['sai'] = DockerShell(
        #     self.container_id,
        #     'sh -c "TERM=dumb bash"',
        #     'root@.*:.*# ',
        #     '/p4factory/targets/switch/tests/pd_thrift/switch_sai_rpc-remote'
        #     ' -h localhost:9092 '
        # )
        #
        # Add switchapi shell
        # https://github.com/p4lang/switch/tree/master/switchapi
        # self._shells['api'] = DockerShell(
        #     self.container_id,
        #     'sh -c "TERM=dumb bash"',
        #     'root@.*:.*# ',
        #     '/p4factory/targets/switch/tests/pd_thrift/switch_api_rpc-remote'
        #     ' -h localhost:9091 '
        # )
        #
        # Add PD shells
        # self._shells['pd_conn_mgr'] = DockerShell(
        #     self.container_id,
        #     'sh -c "TERM=dumb bash"',
        #     'root@.*:.*# ',
        #     '/p4factory/targets/switch/tests/pd_thrift/conn_mgr-remote '
        #     '-h localhost:9090 '
        # )
        # self._shells['pd_mc'] = DockerShell(
        #     self.container_id,
        #     'sh -c "TERM=dumb bash"',
        #     'root@.*:.*# ',
        #     '/p4factory/targets/switch/tests/pd_thrift/mc-remote '
        #     '-h localhost:9090 '
        # )
        # self._shells['pd_p4'] = DockerShell(
        #     self.container_id,
        #     'sh -c "TERM=dumb bash"',
        #     'root@.*:.*# ',
        #     '/p4factory/targets/switch/tests/pd_thrift/dc-remote '
        #     '-h localhost:9090 '
        # )

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

            self._docker_exec(
                'ip link add name veth250 type veth peer name veth251'
            )
            self._docker_exec('ip link set dev veth250 up')
            self._docker_exec('ip link set dev veth251 up')

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
