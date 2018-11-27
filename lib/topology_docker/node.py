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
topology_docker base node module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os import getpid
from json import loads
from os.path import join
from logging import getLogger
from datetime import datetime
from shlex import split as shsplit
from subprocess import check_output
from abc import ABCMeta, abstractmethod

from docker import APIClient
from six import add_metaclass

from topology.platforms.node import CommonNode
from topology_docker.utils import ensure_dir, get_iface_name


log = getLogger(__name__)


@add_metaclass(ABCMeta)
class DockerNode(CommonNode):
    """
    An instance of this class will create a detached Docker container.

    This node binds the ``shared_dir_mount`` directory of the container to a
    local path in the host system defined in ``self.shared_dir``.

    :param str identifier: Node unique identifier in the topology being built.
    :param str image: The image to run on this node, in the
     form ``repository:tag``.
    :param str registry: Docker registry to pull image from.
    :param str command: The command to run when the container is brought up.
    :param str binds: Directories to bind for this container separated by a
     ``;`` in the form:

     ::

        '/tmp:/tmp;/dev/log:/dev/log;/sys/fs/cgroup:/sys/fs/cgroup'

    :param str network_mode: Network mode for this container.
    :param str hostname: Container hostname.
    :param environment: Environment variables to pass to the
     container. They can be set as a list of strings in the following format:

     ::

        ['environment_variable=value']

     or as a dictionary in the following format:

     ::

        {'environment_variable': 'value'}

    :type environment: list or dict
    :param bool privileged: Run container in privileged mode or not.
    :param bool tty: Whether to allocate a TTY or not to the process.
    :param str shared_dir_base: Base path in the host where the shared
     directory will be created. The shared directory will always have the name
     of the container inside this directory.
    :param str shared_dir_mount: Mount point of the shared directory in the
     container.
    :param dict create_host_config_kwargs: Extra kwargs arguments to pass to
     docker-py's ``create_host_config()`` low-level API call.
    :param dict create_container_kwargs: Extra kwargs arguments to pass to
     docker-py's ``create_container()`` low-level API call.

    Read only public attributes:

    :var str image: Name of the Docker image being used by this node.
     Same as the ``image`` keyword argument.
    :var str container_id: Unique container identifier assigned by the Docker
     daemon in the form of a hash.
    :var str container_name: Unique container name assigned by the framework in
     the form ``{identifier}_{pid}_{timestamp}``.
    :var str shared_dir: Share directory in the host for this container. Always
     ``/tmp/topology/{container_name}``.
    :var str shared_dir_mount: Directory inside the container where the
     ``shared_dir`` is mounted. Same as the ``shared_dir_mount`` keyword

    .. automethod:: _get_network_config
    """

    @abstractmethod
    def __init__(
            self, identifier,
            image='ubuntu:latest', registry=None, command='bash',
            binds=None, network_mode='none', hostname=None,
            environment=None, privileged=True, tty=True,
            shared_dir_base='/tmp/topology/docker/',
            shared_dir_mount='/var/topology',
            create_host_config_kwargs=None,
            create_container_kwargs=None,
            **kwargs):

        super(DockerNode, self).__init__(identifier, **kwargs)

        self._pid = None
        self._image = image
        self._registry = registry
        self._command = command
        self._hostname = hostname
        self._environment = environment
        self._client = APIClient(version='auto')

        self._container_name = '{identifier}_{pid}_{timestamp}'.format(
            identifier=identifier, pid=getpid(),
            timestamp=datetime.now().isoformat().replace(':', '-')
        )
        self._shared_dir_base = shared_dir_base
        self._shared_dir_mount = shared_dir_mount
        self._shared_dir = join(
            shared_dir_base,
            self._container_name
        )

        self._create_host_config_kwargs = create_host_config_kwargs or {}
        self._create_container_kwargs = create_container_kwargs or {}

        # Autopull docker image if necessary
        self._autopull()

        # Create shared directory
        ensure_dir(self._shared_dir)

        # Add binded directories
        container_binds = [
            '{}:{}'.format(
                self._shared_dir,
                self._shared_dir_mount
            )
        ]
        if binds is not None:
            container_binds.extend(binds.split(';'))

        # Create host config
        create_host_config_call = {
            'privileged': privileged,
            'network_mode': network_mode,
            'binds': container_binds,
        }
        create_host_config_call.update(self._create_host_config_kwargs)

        self._host_config = self._client.create_host_config(
            **create_host_config_call
        )

        # Create container
        create_container_call = {
            'image': self._image,
            'command': self._command,
            'name': self._container_name,
            'detach': True,
            'tty': tty,
            'hostname': self._hostname,
            'host_config': self._host_config,
            'environment': self._environment,
        }
        create_container_call.update(self._create_container_kwargs)

        self._container_id = self._client.create_container(
            **create_container_call
        )['Id']

    @property
    def image(self):
        return self._image

    @property
    def container_id(self):
        return self._container_id

    @property
    def container_name(self):
        return self._container_name

    @property
    def shared_dir(self):
        return self._shared_dir

    @property
    def shared_dir_mount(self):
        return self._shared_dir_mount

    def _get_network_config(self):
        """
        Defines the network configuration for nodes of this type.

        This method should be overriden when implementing a new node type to
        return a dictionary with its network configuration by setting the
        following components:

        'mapping'
            This is a dictionary of dictionaries, each parent-level key defines
            one network category, and each category *must* have these three
            keys: **netns**, **managed_by**, and **prefix**, and *can*
            (optionally) have a **connect_to** key).

            'netns'
                Specifies the network namespace (inside the docker container)
                where all the ports belonging to this category will be moved
                after their creation. If set to None, then the ports will
                remain in the container's default network namespace.

            'managed_by'
                Specifies who will manage different aspects of this network
                category depending on its value (which can be either **docker**
                or **platform**).

                'docker'
                    This network category will represent a network created by
                    docker (identical to using the docker network create
                    command) and will be visible to docker (right now all
                    docker-managed networks are created using docker's 'bridge'
                    built-in network plugin, this will likely change in the
                    near future).

                'platform'
                    This network category will represent ports created by the
                    Docker Platform Engine and is invisible to docker.

            'prefix'
                Defines a prefix that will be used when a port/interface is
                moved into a namespace, its value can be set to '' (empty
                string) if no prefix is needed. In cases where the parent
                network category doesn't have a netns (i.e. 'netns' is set to
                None) this value will be ignored.

            'connect_to'
                Specifies a Docker network this category will be connected to,
                if this network doesn't exists it will be created. If set to
                None, this category will be connected to a uniquely named
                Docker network that will be created by the platform.

        'default_category'
            Every port that didn't explicitly set its category (using the
            "category" attribute in the SZN definition) will be set to this
            category.

        This is an example of a network configuration dictionary as expected to
        be returned by this funcition::

            {
                'default_category': 'front_panel',
                'mapping': {
                    'oobm': {
                        'netns': 'oobmns',
                        'managed_by': 'docker',
                        'connect_to': 'oobm'
                        'prefix': ''
                    },
                    'back_panel': {
                        'netns': None,
                        'managed_by': 'docker',
                        'prefix': ''
                    },
                    'front_panel': {
                        'netns': 'front',
                        'managed_by': 'platform',
                        'prefix': 'f_'
                    }
                }
            }

        :returns: The dictionary defining the network configuration.
        :rtype: dict
        """
        return {
            'default_category': 'front_panel',
            'mapping': {
                'oobm': {
                    'netns': None,
                    'managed_by': 'docker',
                    'prefix': ''
                },
                'front_panel': {
                    'netns': 'front_panel',
                    'managed_by': 'platform',
                    'prefix': ''
                }
            }
        }

    def _autopull(self):
        """
        Autopulls the docker image of the node, if necessary.
        """
        # Search for image in available images
        for tags in [img['RepoTags'] for img in self._client.images()]:
            # Docker py can return repo tags as None
            if tags and self._image in tags:
                return

        # Determine image parts
        registry = self._registry
        image = self._image
        tag = 'latest'

        if ':' in image:
            image, tag = image.split(':')

        # Pull image
        pull_uri = image
        if registry:
            pull_uri = '{}/{}'.format(registry, image)
        pull_name = '{}:{}'.format(pull_uri, tag)

        log.info('Trying to pull image {} ...'.format(pull_name))

        last = ''
        for line in self._client.pull(pull_uri, tag=tag, stream=True):
            last = line
        status = loads(last.decode('utf8'))

        log.debug('Pulling result :: {}'.format(status))

        if 'error' in status:
            raise Exception(status['error'])

        # Retag if required
        if pull_name != self._image:
            if not self._client.tag(pull_name, image, tag):
                raise Exception(
                    'Error when tagging image {} with tag {}:{}'.format(
                        pull_name, image, tag
                    )
                )

            log.info(
                'Tagged image {} with tag {}:{}'.format(
                    pull_name, image, tag
                )
            )

    def _docker_exec(self, command):
        """
        Execute a command inside the docker.

        :param str command: The command to execute.
        """
        log.debug(
            '[{}]._docker_exec(\'{}\') ::'.format(self._container_id, command)
        )

        response = check_output(shsplit(
            'docker exec {container_id} {command}'.format(
                container_id=self._container_id, command=command.strip()
            )
        )).decode('utf8')

        log.debug(response)
        return response

    def _get_services_address(self):
        """
        Get the service address of the node using Docker's inspect mechanism
        to grab OOBM interface address.

        :return: The address (IP or FQDN) of the services interface (oobm).
        :rtype: str
        """
        network_name = self._container_name + '_oobm'
        address = self._client.inspect_container(
            self.container_id
        )['NetworkSettings']['Networks'][network_name]['IPAddress']
        return address

    def notify_add_biport(self, node, biport):
        """
        Get notified that a new biport was added to this engine node.

        :param node: The specification node that spawn this engine node.
        :type node: pynml.nml.Node
        :param biport: The specification bidirectional port added.
        :type biport: pynml.nml.BidirectionalPort
        :rtype: str
        :return: The assigned interface name of the port.
        """

        network_config = self._get_network_config()

        category = biport.metadata.get(
            'category',
            network_config['default_category']
        )
        category_config = network_config['mapping'][category]

        if category_config['managed_by'] is 'docker':
            netname = category_config.get(
                'connect_to',
                '{}_{}'.format(self._container_name, category)
            )
            return get_iface_name(self, netname)
        else:
            return biport.metadata.get('label', biport.identifier)

    def notify_add_bilink(self, nodeport, bilink):
        """
        Get notified that a new bilink was added to a port of this engine node.

        :param nodeport: A tuple with the specification node and port being
         linked.
        :type nodeport: (pynml.nml.Node, pynml.nml.BidirectionalPort)
        :param bilink: The specification bidirectional link added.
        :type bilink: pynml.nml.BidirectionalLink
        """

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.
        """
        # Log container data
        image_data = self._client.inspect_image(
            image=self._image
        )
        log.info(
            'Started container {}:\n'
            '    Image name: {}\n'
            '    Image id: {}\n'
            '    Image creation date: {}'
            '    Image tags: {}'.format(
                self._container_name,
                self._image,
                image_data.get('Id', '????'),
                image_data.get('Created', '????'),
                ', '.join(image_data.get('RepoTags', []))
            )
        )
        container_data = self._client.inspect_container(
            container=self._container_id
        )
        log.debug(container_data)

    def start(self):
        """
        Start the docker node and configures a netns for it.
        """
        self._client.start(self._container_id)
        self._pid = self._client.inspect_container(
            self._container_id)['State']['Pid']

    def stop(self):
        """
        Request container to stop.
        """
        self._client.stop(self._container_id)
        self._client.wait(self._container_id)
        self._client.remove_container(self._container_id)

    def disable(self):
        """
        Disable the node.

        In Docker implementation this pauses the container.
        """
        for portlbl in self.ports:
            self.set_port_state(portlbl, False)
        self._client.pause(self._container_id)

    def enable(self):
        """
        Enable the node.

        In Docker implementation this unpauses the container.
        """
        self._client.unpause(self._container_id)
        for portlbl in self.ports:
            self.set_port_state(portlbl, True)

    def set_port_state(self, portlbl, state):
        """
        Set the given port label to the given state.

        :param str portlbl: The label of the port.
        :param bool state: True for up, False for down.
        """
        iface = self.ports[portlbl]
        state = 'up' if state else 'down'

        command = (
            'ip netns exec front_panel '
            'ip link set dev {iface} {state}'.format(**locals())
        )
        self._docker_exec(command)


__all__ = ['DockerNode']
