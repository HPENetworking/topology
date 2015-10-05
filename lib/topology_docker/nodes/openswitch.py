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

from os import environ
from os.path import isfile
from time import sleep

from yaml import load

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell
from topology_docker.utils import ensure_dir


WAIT_FOR_OPENSWITCH = """\
#!/usr/bin/env python

from time import sleep
from os.path import exists
from json import dumps, loads
from socket import AF_UNIX, SOCK_STREAM, socket

db_sock = '/var/run/openvswitch/db.sock'
switchd_pid = '/var/run/openvswitch/ops-switchd.pid'
query = {
    'method': 'transact',
    'params': [
        'OpenSwitch',
        {
            'op': 'select',
            'table': 'System',
            'where': [],
            'columns': ['cur_hw']
        }
    ],
    'id': id(db_sock)
}
sock = None


def cur_cfg_is_set():
    global sock
    if sock is None:
        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.connect(db_sock)
    sock.send(dumps(query))
    response = loads(sock.recv(4096))
    return response['result'][0]['rows'][0]['cur_hw'] == 1


def main():
    while not exists(db_sock):
        sleep(0.1)
    while not cur_cfg_is_set():
        sleep(0.1)
    while not exists(switchd_pid):
        sleep(0.1)

if __name__ == '__main__':
    main()
"""


class OpenSwitchNode(DockerNode):
    """
    Custom engine node for the Topology docker platform engine.

    This custom node loads an OpenSwitch image and has vtysh as default
    console (in addition to bash).

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node. The image can also be
     setup using the environment variable ``OPS_IMAGE``. If present, it will
     take precedence to this argument in runtime.
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
            image='ops:latest', command='/sbin/init', binds=None,
            **kwargs):

        # Fetch image from environment
        image = environ.get('OPS_IMAGE', image)

        # Determine shared directory
        shared_dir = '/tmp/topology_{}'.format(identifier)
        ensure_dir(shared_dir)

        # Add binded directories
        if binds is None:
            binds = []
        binds.extend([
            '{}:/tmp'.format(shared_dir),
            '/dev/log:/dev/log',
            '/sys/fs/cgroup:/sys/fs/cgroup:ro'
        ])

        super(OpenSwitchNode, self).__init__(
            identifier, image=image, command=command, binds=binds, **kwargs
        )

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

        # Add vtysh (default) and bash shell
        self._shells['vtysh'] = DockerShell(
            self.identifier, 'vtysh', 'switch.*#'
        )
        self._shells['bash'] = DockerShell(
            self.identifier, 'bash', 'bash-.*#'
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        super(OpenSwitchNode, self).notify_post_build()

        # Wait for swns to be available
        while 'swns' not in self.send_command('ip netns list', shell='bash'):
            sleep(0.1)

        # Move interfaces to swns network namespace and rename port interfaces
        cmd_tpl = """\
            ip link set {iface} netns swns
            ip netns exec swns ip link set {iface} name {port_number}\
        """
        # List of all created interfaces
        ifaces = []

        for port_spec in self._ports.values():
            netns, rename = [
                cmd.strip() for cmd in cmd_tpl.format(**port_spec).splitlines()
            ]

            # Set interfaces in swns namespace
            assert not self.send_command(netns, shell='bash')

            # Named interfaces are ignored
            if port_spec['port_number'] is None:
                ifaces.append(port_spec['iface'])
                continue

            # Rename numbered interfaces
            assert not self.send_command(rename, shell='bash')
            ifaces.append(str(port_spec['port_number']))

        # TODO: Analyse the option to comment this lines,
        #       they take too much time. Are they really required?
        self._create_hwdesc_ports(ifaces)
        self._wait_system_setup()

    def _create_hwdesc_ports(self, exclude):
        """
        Create all ports in the hardware description.

        :param list exclude: List of ports to exclude. Usually the ports
         already created.
        """
        # Wait for daemons to be ready
        while 'hwdesc' not in self.send_command(
                'ls /etc/openswitch/', shell='bash').split():
            sleep(0.1)

        # Read hardware description for ports
        assert not self.send_command(
            'cp /etc/openswitch/hwdesc/ports.yaml /tmp/',
            shell='bash'
        )

        with open('{}/ports.yaml'.format(self.shared_dir), 'r') as fd:
            ports_hwdesc = load(fd)
        hwports = [str(p['name']) for p in ports_hwdesc['ports']]

        # Create remaining ports
        cmd_tpl = """\
            ip tuntap add dev {hwport} mode tap
            ip link set {hwport} netns swns\
        """

        for hwport in hwports:
            if hwport in exclude:
                continue

            commands = [
                cmd.strip() for cmd in
                cmd_tpl.format(hwport=hwport).splitlines()
            ]
            for cmd in commands:
                assert not self.send_command(cmd, shell='bash')

    def _wait_system_setup(self):
        """
        Wait until OpenSwitch daemons converge.
        """
        wait_script = '{}/wait_for_openswitch'.format(self.shared_dir)
        if not isfile(wait_script):
            with open(wait_script, 'w') as fd:
                fd.write(WAIT_FOR_OPENSWITCH)
            assert not self.send_command(
                'chmod +x /tmp/wait_for_openswitch',
                shell='bash'
            )
        assert not self.send_command('/tmp/wait_for_openswitch', shell='bash')


__all__ = ['OpenSwitchNode']
