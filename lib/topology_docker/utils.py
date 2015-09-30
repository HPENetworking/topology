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
topology_docker utilities module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from os import getuid, devnull
from subprocess import call
from shlex import split as shsplit


log = logging.getLogger(__name__)


def iface_name(node, port):
    """
    Get the interface name for a given specification node and port.

    :param node: The specification node owner of the port.
    :type node: pynml.nml.Node
    :param biport: The specification port representing the interface.
    :type biport: pynml.nml.BidirectionalPort
    :rtype: str
    :return: The name of the interface.
    """
    if 'port_number' in port.metadata:
        return '{}-{}'.format(
            node.identifier,
            port.metadata['port_number']
        )
    return port.identifier


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


__all__ = ['iface_name', 'cmd_prefix']
