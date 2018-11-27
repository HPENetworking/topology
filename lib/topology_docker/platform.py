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
Docker engine platform module for topology.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from traceback import format_exc
from collections import OrderedDict
from docker import APIClient

from topology.platforms.utils import NodeLoader
from topology.platforms.platform import BasePlatform

from .node import DockerNode
from .utils import tmp_iface, privileged_cmd
from .networks import create_docker_network, create_platform_network


log = logging.getLogger(__name__)


class DockerPlatform(BasePlatform):
    """
    Plugin to build a topology using Docker.

    See :class:`topology.platforms.platform.BasePlatform` for more information.
    """

    def __init__(self, timestamp, nmlmanager):

        self.node_loader = NodeLoader(
            'docker', api_version='1.0', base_class=DockerNode
        )

        self.nmlnode_node_map = OrderedDict()
        self.nmlbiport_iface_map = OrderedDict()
        self.nmlbilink_nmlbiports_map = OrderedDict()
        self.available_node_types = self.node_loader.load_nodes()

        # Create netns folder
        privileged_cmd('mkdir -p /var/run/netns')

    def pre_build(self):
        """
        See :meth:`BasePlatform.pre_build` for more information.
        """

    def add_node(self, node):
        """
        Add a new DockerNode.

        See :meth:`BasePlatform.add_node` for more information.
        """
        # Lookup for node of given type
        node_type = node.metadata.get('type', 'host')
        if node_type not in self.available_node_types:
            raise Exception('Unknown node type {}'.format(node_type))

        # Create instance of node type and start
        enode = self.available_node_types[node_type](
            node.identifier, **node.metadata
        )

        # Register node
        self.nmlnode_node_map[node.identifier] = enode

        # Start node
        enode.start()

        # Install container netns locally
        privileged_cmd(
            'ln -s /proc/{pid}/ns/net /var/run/netns/{pid}',
            pid=enode._pid
        )

        # Manage network and their netns creation
        network_handlers = {
            'docker': create_docker_network,
            'platform': create_platform_network
        }

        for category, config in enode._get_network_config()['mapping'].items():

            managed_by = config['managed_by']
            handler = network_handlers.get(managed_by, None)

            if handler is None:
                raise RuntimeError(
                    'Unknown "managed_by" handler {}'.format(managed_by)
                )

            handler(enode, category, config)

        return enode

    def add_biport(self, node, biport):
        """
        Add a port to the docker node.

        See :meth:`BasePlatform.add_biport` for more information.
        """
        enode = self.nmlnode_node_map[node.identifier]
        eport = enode.notify_add_biport(node, biport)

        # Get network configuration of given port
        network_config = enode._get_network_config()

        category = biport.metadata.get(
            'category',
            network_config['default_category']
        )
        category_config = network_config['mapping'][category]

        # If this port is from a docker-managed network, then it will be
        # created when this node was connected to the network
        created = True if category_config['managed_by'] == 'docker' else False

        # Register this port for later creation
        self.nmlbiport_iface_map[biport.identifier] = {
            'created': created,
            'iface_base': eport,
            'prefix': category_config['prefix'],
            'iface': '{}{}'.format(category_config['prefix'], eport),
            'container_ns': enode._pid,
            'netns': category_config['netns'],
            'owner': node.identifier,
            'label': biport.metadata.get('label', biport.identifier)
        }

        return eport

    def add_bilink(self, nodeport_a, nodeport_b, bilink):
        """
        Add a link between two nodes.

        See :meth:`BasePlatform.add_bilink` for more information.
        """
        node_a, port_a = nodeport_a
        node_b, port_b = nodeport_b

        # Get enodes
        enode_a = self.nmlnode_node_map[node_a.identifier]
        enode_b = self.nmlnode_node_map[node_b.identifier]

        # Determine temporal interfaces names
        tmp_iface_a = tmp_iface()
        tmp_iface_b = tmp_iface()

        # Get port spec dictionary
        port_spec_a = self.nmlbiport_iface_map[port_a.identifier]
        port_spec_b = self.nmlbiport_iface_map[port_b.identifier]

        # If any of the ports is already created then don't do anything here
        # FIXME: We should probably let the user know if one of the ports is
        # created and the other is not, as this case is undefined and
        # unsupported
        if port_spec_a['created'] or port_spec_b['created']:
            return

        # Determine final interface names
        iface_a = port_spec_a['iface']
        iface_b = port_spec_b['iface']

        # Create links between nodes:
        #   docs.docker.com/v1.5/articles/networking/#building-a-point-to-point-connection # noqa
        commands = """\
        ip link add {tmp_iface_a} type veth peer name {tmp_iface_b}
        ip link set {tmp_iface_a} netns {enode_a._pid} name {iface_a}
        ip link set {tmp_iface_b} netns {enode_b._pid} name {iface_b}\
        """
        privileged_cmd(commands, **locals())

        # Apply some attributes to nodes and ports
        for enode, port, port_spec, iface in (
            (enode_a, port_a, port_spec_a, iface_a),
            (enode_b, port_b, port_spec_b, iface_b)
        ):

            # Move interfaces to correct network namespace
            netns = port_spec['netns']
            if netns:
                enode._docker_exec(
                    'ip link set dev {iface} netns {netns}'.format(
                        **locals()
                    )
                )
                cmd_prefix = 'ip netns exec {netns} '.format(**locals())
            else:
                cmd_prefix = ''

            # Set ipv4 and ipv6 addresses
            for version in [4, 6]:
                attribute = 'ipv{}'.format(version)
                if attribute not in port.metadata:
                    continue

                addr = port.metadata[attribute]
                cmd = (
                    '{cmd_prefix}ip -{version} addr add {addr} dev {iface}'
                ).format(**locals())
                enode._docker_exec(cmd)

            # Bring-up or down
            if bilink.metadata.get('up', None) is None and \
                    port.metadata.get('up', None) is None:
                continue

            up = bilink.metadata.get('up', True) and \
                port.metadata.get('up', True)

            state = 'up' if up else 'down'
            cmd = '{cmd_prefix}ip link set dev {iface} {state}'.format(
                **locals()
            )
            enode._docker_exec(cmd)

        # Notify enodes of created interfaces
        enode_a.notify_add_bilink(nodeport_a, bilink)
        enode_b.notify_add_bilink(nodeport_b, bilink)

        # Mark interfaces as created
        self.nmlbiport_iface_map[port_a.identifier]['created'] = True
        self.nmlbiport_iface_map[port_b.identifier]['created'] = True

        # Register these links
        self.nmlbilink_nmlbiports_map[bilink.identifier] = (
            port_a.identifier, port_b.identifier
        )

    def post_build(self):
        """
        Ports are created for each node automatically while adding links.
        Creates the rest of the ports (no-linked ports)

        See :meth:`BasePlatform.post_build` for more information.
        """
        # Create remaining interfaces
        cmd_tpl = (
            'ip netns exec {container_ns} '
            'ip tuntap add dev {iface} mode tap'
        )
        for port_spec in self.nmlbiport_iface_map.values():

            # Ignore already created interfaces
            if port_spec['created']:
                continue

            # Create port as dummy tuntap device
            privileged_cmd(cmd_tpl, **port_spec)

            # Move port to network namespace if required
            if port_spec['netns']:
                enode = self.nmlnode_node_map[port_spec['owner']]
                enode._docker_exec(
                    'ip link set dev {iface} netns {netns}'.format(
                        **port_spec
                    )
                )

            # Mark as created
            port_spec['created'] = True

        # Notify nodes of the post_build event
        for enode in self.nmlnode_node_map.values():
            enode.notify_post_build()

    def destroy(self):
        """
        See :meth:`BasePlatform.destroy` for more information.
        """
        # NOTE: Implementation is split on purpose

        # Request termination of all containers
        for enode in self.nmlnode_node_map.values():
            try:
                enode.stop()
            except Exception:
                log.error(format_exc())

        # Remove the linked netns
        for enode in self.nmlnode_node_map.values():
            try:
                privileged_cmd('rm /var/run/netns/{pid}', pid=enode._pid)
            except Exception:
                log.error(format_exc())

        # Save the names of all docker-managed networks
        networks_to_remove = set()
        for enode in self.nmlnode_node_map.values():
            try:
                network_config = enode._get_network_config()['mapping']

                for category, config in network_config.items():
                    if config['managed_by'] == 'docker':
                        netname = config.get('connect_to', None)
                        if netname is None:

                            netname = '{}_{}'.format(
                                enode._container_name,
                                category
                            )

                        networks_to_remove.add(netname)

            except Exception:
                log.error(format_exc())

        # Remove all docker-managed networks
        dockerclient = APIClient(version='auto')
        for netname in networks_to_remove:
            dockerclient.remove_network(net_id=netname)

    def rollback(self, stage, enodes, exception):
        """
        See :meth:`BasePlatform.rollback` for more information.
        """
        self.destroy()

    def _common_link(self, link_id, action):
        """
        Common action to relink / unlink.

        :param str link_id: Identifier of the link to modify.
        :param bool action: True if up, False if down.
        """
        if link_id not in self.nmlbilink_nmlbiports_map:
            raise Exception('Unknown link "{}"'.format(link_id))

        # iterate endpoints
        for port_id in self.nmlbilink_nmlbiports_map[link_id]:

            # Get specification for this endpoint
            port_spec = self.nmlbiport_iface_map[port_id]

            # Get node for the owner of this port
            enode = self.nmlnode_node_map[port_spec['owner']]
            enode.set_port_state(port_spec['label'], action)

    def relink(self, link_id):
        """
        See :meth:`BasePlatform.relink` for more information.
        """
        self._common_link(link_id, True)

    def unlink(self, link_id):
        """
        See :meth:`BasePlatform.unlink` for more information.
        """
        self._common_link(link_id, False)


__all__ = ['DockerPlatform']
