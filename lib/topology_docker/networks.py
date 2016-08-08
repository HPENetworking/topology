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
Docker networks management module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from topology_docker.utils import get_iface_name


log = logging.getLogger(__name__)


def create_docker_network(enode, category, config):
    """
    Create a Docker managed network with given configuration (netns, prefix) to
    be used with Topology framework.

    :param enode: The platform (a.k.a "engine") node to configure.
    :param str category: Name of the panel category.
    :param dict config: Configuration for the network. A dictionary like:

     ::

        {
            'netns': 'mynetns',
            'managed_by': 'docker',
            'connect_to': 'somedockernetwork',
            'prefix': ''
        }

     This dictionary is taken from the ``node._get_network_config()`` result.
    """
    # Let's find out which networks exist already
    dockernets = enode._client.networks()

    # Let's figure out what docker network we should connect to
    netname = config.get(
        'connect_to',
        '{}_{}'.format(enode._container_name, category)
    )

    # Create docker network if it doesn't exist already
    if not any(d['Name'] == netname for d in dockernets):
        enode._client.create_network(
            name=netname,
            driver='bridge'
        )

    # Disconnect from 'none' to be able to connect to other
    # networks (https://github.com/docker/docker/issues/21132)
    networks = enode._client.inspect_container(
        enode.container_id
    )['NetworkSettings']['Networks']
    if 'none' in networks:
        enode._client.disconnect_container_from_network(
            container=enode._container_id,
            net_id='none'
        )

    # Connect container to the docker network
    enode._client.connect_container_to_network(
        container=enode._container_id,
        net_id=netname
    )

    # Check if this category has a defined netns
    netns = config.get('netns', None)
    if netns is None:
        return

    # Create this network's namespace inside the container
    # https://imgflip.com/i/16621d
    enode._docker_exec('ip netns add {}'.format(netns))

    netns_exec = 'ip netns exec {}'.format(netns)

    # lo should always be up
    enode._docker_exec('{} ip link set dev lo up'.format(netns_exec))

    # Find out the name Docker gave to this interface name
    iface = get_iface_name(enode, netname)

    # Prefix interface
    prefixed_iface = '{}{}'.format(config['prefix'], iface)

    # Move this network's interface to its netns
    enode._docker_exec(
        'ip link set dev {iface} netns {netns} name {prefixed_iface}'.format(
            **locals()
        )
    )

    # Reset the interface to original config
    # This is required because after moving the iface from netns it lost its
    # ip and other config.
    enode._docker_exec(
        '{netns_exec} '
        'ip address add {docker_netconf[IPAddress]}/'
        '{docker_netconf[IPPrefixLen]} '
        'dev {prefixed_iface}'.format(
            **locals()
        )
    )
    enode._docker_exec(
        '{netns_exec} ip link set dev {prefixed_iface} up'.format(
            **locals()
        )
    )


def create_platform_network(enode, category, config):
    """
    Create a Topology managed network with given configuration (netns, prefix).

    :param enode: The platform (a.k.a "engine") node to configure.
    :param str category: Name of the panel category.
    :param dict config: Configuration for the network. A dictionary like:

     ::

        {
            'netns': 'mynetns',
            'managed_by': 'platform',
            'prefix': ''
        }

     This dictionary is taken from the ``node._get_network_config()`` result.
    """
    # Check if this category has a defined netns
    netns = config.get('netns', None)
    if netns is None:
        return

    # Create the given network namespace
    enode._docker_exec('ip netns add {}'.format(netns))

    # lo should always be up
    enode._docker_exec('ip netns exec {} ip link set dev lo up'.format(netns))


__all__ = ['create_docker_network', 'create_platform_network']
