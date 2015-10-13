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
from subprocess import check_call
from shlex import split as shsplit

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell
from topology_docker.utils import ensure_dir


SETUP_SCRIPT = """\
#!/usr/bin/env python

from sys import argv
from time import sleep
from os.path import exists
from json import dumps, loads
from subprocess import check_call
from shlex import split as shsplit
from socket import AF_UNIX, SOCK_STREAM, socket

import yaml

swns_netns = '/var/run/netns/swns'
hwdesc_dir = '/etc/openswitch/hwdesc'
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


def create_interfaces():
    with open('{}/ports.yaml'.format(hwdesc_dir), 'r') as fd:
        ports_hwdesc = yaml.load(fd)

    hwports = [str(p['name']) for p in ports_hwdesc['ports']]
    exclude = argv[1:]

    # Create remaining ports
    create_cmd_tpl = 'ip tuntap add dev {hwport} mode tap'
    netns_cmd_tpl = 'ip link set {hwport} netns swns'

    for hwport in hwports:
        if hwport in exclude:

            # Move numeric interfaces to the swns netns
            if hwport.isdigit():
                check_call(shsplit(netns_cmd_tpl.format(hwport=hwport)))
            continue

        check_call(shsplit(create_cmd_tpl.format(hwport=hwport)))
        check_call(shsplit(netns_cmd_tpl.format(hwport=hwport)))


def cur_cfg_is_set():
    global sock
    if sock is None:
        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.connect(db_sock)
    sock.send(dumps(query))
    response = loads(sock.recv(4096))
    return response['result'][0]['rows'][0]['cur_hw'] == 1


def main():
    while not exists(swns_netns):
        sleep(0.1)
    while not exists(hwdesc_dir):
        sleep(0.1)

    create_interfaces()

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

        # Fetch image from environment but only if default image is being used
        if image == 'ops:latest':
            image = environ.get('OPS_IMAGE', image)

        # Determine shared directory
        shared_dir = '/tmp/topology_{}_{}'.format(identifier, str(id(self)))
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
            self.container_id, 'vtysh', 'switch.*#'
        )
        self._shells['bash'] = DockerShell(
            self.container_id, 'sh -c "TERM=dumb bash"', 'bash-.*#'
        )
        self._shells['bash_swns'] = DockerShell(
            self.container_id,
            'sh -c "TERM=dumb ip netns exec swns bash"',
            'bash-.*#'
        )
        self._shells['vsctl'] = DockerShell(
            self.container_id, 'sh -c "TERM=dumb bash"', 'bash-.*#',
            prefix='ovs-vsctl ', timeout=60
        )

        # Store all externally created interfaces
        self._ifaces = []

    def notify_add_biport(self, node, biport):
        """
        Get notified that a new biport was added to this engine node.

        See :meth:`DockerNode.notify_add_biport` for more information.
        """
        iface = super(OpenSwitchNode, self).notify_add_biport(node, biport)
        self._ifaces.append(iface)
        return iface

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """
        super(OpenSwitchNode, self).notify_post_build()

        # TODO: Analyse the option to comment this lines,
        #       they take too much time. Are they really required?
        self._setup_system(self._ifaces)

    def _setup_system(self, exclude):
        """
        Setup the OpenSwitch image for testing.

        #. Create remaining interfaces.
        #. Wait for daemons to converge.

        :param list exclude: List of ports to exclude. Usually the ports
         already created.
        """
        setup_script = '{}/openswitch_setup.py'.format(self.shared_dir)
        if not isfile(setup_script):
            with open(setup_script, 'w') as fd:
                fd.write(SETUP_SCRIPT)

        check_call(shsplit(
            'docker exec {} python /tmp/openswitch_setup.py {}'.format(
                self.container_id, ' '.join(exclude)
            )
        ))


__all__ = ['OpenSwitchNode']
