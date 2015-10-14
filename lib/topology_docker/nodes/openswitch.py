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
import logging
from sys import argv
from time import sleep
from os.path import exists
from json import dumps, loads
from shlex import split as shsplit
from subprocess import check_call, check_output
from socket import AF_UNIX, SOCK_STREAM, socket, gethostname

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
    # Read ports from hardware description
    with open('{}/ports.yaml'.format(hwdesc_dir), 'r') as fd:
        ports_hwdesc = yaml.load(fd)
    hwports = [str(p['name']) for p in ports_hwdesc['ports']]

    # Get list of already created ports
    not_in_swns = check_output(shsplit(
        'ls /sys/class/net/'
    )).split()
    in_swns = check_output(shsplit(
        'ip netns exec swns ls /sys/class/net/'
    )).split()

    create_cmd_tpl = 'ip tuntap add dev {hwport} mode tap'
    netns_cmd_tpl = 'ip link set {hwport} netns swns'

    for hwport in hwports:
        if hwport in in_swns:
            logging.info('  - Port {} already present.'.format(hwport))
            continue

        if hwport in not_in_swns:
            logging.info('  - Port {} moved to swns netns.'.format(hwport))
            check_call(shsplit(netns_cmd_tpl.format(hwport=hwport)))
            continue

        logging.info('  - Port {} created.'.format(hwport))
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

    if '-d' in argv:
        logging.basicConfig(level=logging.DEBUG)

    logging.info('Waiting for swns netns...')
    while not exists(swns_netns):
        sleep(0.1)

    logging.info('Waiting for hwdesc directory...')
    while not exists(hwdesc_dir):
        sleep(0.1)

    logging.info('Creating interfaces...')
    create_interfaces()

    logging.info('Waiting for DB socket...')
    while not exists(db_sock):
        sleep(0.1)

    logging.info('Waiting for cur_cfg...')
    while not cur_cfg_is_set():
        sleep(0.1)

    logging.info('Waiting for switchd pid...')
    while not exists(switchd_pid):
        sleep(0.1)

    logging.info('Wait for final hostname...')
    while gethostname() != 'switch':
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

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """
        super(OpenSwitchNode, self).notify_post_build()
        self._setup_system()

    def _setup_system(self):
        """
        Setup the OpenSwitch image for testing.

        #. Create remaining interfaces.
        #. Wait for daemons to converge.
        """
        setup_script = '{}/openswitch_setup.py'.format(self.shared_dir)
        if not isfile(setup_script):
            with open(setup_script, 'w') as fd:
                fd.write(SETUP_SCRIPT)

        check_call(shsplit(
            'docker exec {} python /tmp/openswitch_setup.py'.format(
                self.container_id
            )
        ))


__all__ = ['OpenSwitchNode']
