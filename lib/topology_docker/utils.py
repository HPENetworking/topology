# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Hewlett Packard Enterprise Development LP
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
topology_docker utilities module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from os import getuid, devnull, makedirs
from shlex import split as shsplit
from subprocess import call, check_call


log = logging.getLogger(__name__)


def ensure_dir(path):
    """
    Ensure that a path exists.

    :param str path: Directory path to create.
    """
    import errno
    EEXIST = getattr(errno, 'EEXIST', 0)  # noqa

    try:
        makedirs(path)
    except OSError as err:
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise


IFNAMSIZ = 15
"""
This is the maximum length a network interface can have.
Defined in linux/if.h as 16, but counting the termination character.
"""


def tmp_iface():
    """
    Return a valid temporal interface name.

    :rtype: str
    :return: A random valid network interface name.
    """
    import random
    import string
    return ''.join(
        random.choice(string.ascii_lowercase)
        for _ in range(IFNAMSIZ)
    )


def cmd_prefix():
    """
    Determine if the current user can run privileged commands and thus
    determines the command prefix to use.

    :rtype: str
    :return: The prefix to use for privileged commands.
    """

    # Return cache if set
    if hasattr(cmd_prefix, 'prefix'):
        return cmd_prefix.prefix

    if getuid() == 0:
        # We better do not allow root
        raise RuntimeError(
            'Please do not run as root. '
            'Please configure the ip command for root execution.'
        )
        # cmd_prefix.prefix = ''
        # return cmd_prefix.prefix

    with open(devnull, 'w') as f:
        cmd = shsplit('sudo --non-interactive ip link show')
        if call(cmd, stdout=f, stderr=f) != 0:
            raise RuntimeError(
                'Please configure the ip command for root execution.'
            )

    cmd_prefix.prefix = 'sudo --non-interactive '
    return cmd_prefix.prefix


def privileged_cmd(commands_tpl, **kwargs):
    """
    Run a privileged command.

    This function will replace the tokens in the template with the provided
    keyword arguments, then it will split the lines of the template, strip
    them and execute them using the prefix for privileged commands, checking
    that the command returns 0.

    :param str commands_tpl: Single line or multiline template for commands.
    :param dict kwargs: Replacement tokens.
    """
    prefix = cmd_prefix()

    for command in commands_tpl.format(**kwargs).splitlines():
        command = command.strip()
        if command:
            check_call(shsplit(prefix + command))


def get_iface_name(enode, netname):
    """
    Get interface name inside a container

    This function will figure out the interface name inside the container for
    a given docker network.

    :param enode: The platform ("engine") node to get the iface name from.
    :param str netname: The name of the docker network to which the interface
                        we're looking for is connected.
    """
    # FIXME: there must be a better way to do this, and we're not the only ones
    # that think so, (see: https://github.com/docker/docker/issues/17064)
    docker_netconf = enode._client.inspect_container(
        enode.container_id
    )['NetworkSettings']['Networks'][netname]

    ifaces_conf = enode._docker_exec(
        'ip -o link list'
    ).strip().split('\n')

    for iface_conf in ifaces_conf:
        if docker_netconf['MacAddress'] in iface_conf:
            iface = iface_conf.split(': ')[1].split('@')[0]
            break
    else:
        raise RuntimeError(
            'Unable to find interface with MAC address '
            '{docker_netconf[MacAddress]} in netns {netns} in container '
            '{enode._container_id} with name '
            '{enode._container_name}'.format(
                **locals()
            )
        )

    return iface


__all__ = [
    'ensure_dir',
    'tmp_iface',
    'cmd_prefix',
    'privileged_cmd',
    'get_iface_name'
]
