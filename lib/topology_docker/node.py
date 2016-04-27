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
topology_docker base node module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from json import loads
from logging import getLogger
from shlex import split as shsplit
from subprocess import check_output
from abc import ABCMeta, abstractmethod

from docker import Client
from six import add_metaclass

from topology.platforms.base import CommonNode
from topology_docker.utils import ensure_dir


log = getLogger(__name__)


@add_metaclass(ABCMeta)
class DockerNode(CommonNode):
    """
    An instance of this class will create a detached Docker container.

    This node binds the ``/tmp/`` directory of the container to a local path
    in the host system under ``/tmp/topology_{identifier}_{uuid}/``. This value
    is stored under ``node.shared_dir`` attribute and can be used to share
    files.

    :param str identifier: The unique identifier of the node.
    :param str image: The image to run on this node, in the
     form ``repository:tag``.
    :param str registry: Docker registry to pull image from.
    :param str command: The command to run when the container is brought up.
    :param str binds: Directories to bind for this container separated by a
     ``;`` in the form:

     ::

        '/tmp:/tmp;/dev/log:/dev/log;/sys/fs/cgroup:/sys/fs/cgroup'

    :param str network_mode: Network mode for this container.
    """

    @abstractmethod
    def __init__(
            self, identifier,
            image='ubuntu:latest', registry=None, command='bash',
            binds=None, network_mode='none', hostname=None, **kwargs):

        super(DockerNode, self).__init__(identifier, **kwargs)

        self._pid = None
        self._image = image
        self._registry = registry
        self._command = command
        self._hostname = hostname
        self._client = Client(version='auto')

        # Autopull docker image if necessary
        self._autopull()

        # Create shared directory
        self.shared_dir = '/tmp/topology/{}_{}'.format(
            identifier, str(id(self))
        )
        ensure_dir(self.shared_dir)

        # Add binded directories
        container_binds = [
            '{}:/tmp'.format(self.shared_dir)
        ]
        if binds is not None:
            container_binds.extend(binds.split(';'))

        # Create host config
        self._host_config = self._client.create_host_config(
            # Container is given access to all devices
            privileged=True,
            # Avoid connecting to host bridge, usually docker0
            network_mode=network_mode,
            binds=container_binds
        )

        # Create container
        self.container_id = self._client.create_container(
            image=self._image,
            command=self._command,
            name='{}_{}'.format(identifier, str(id(self))),
            detach=True,
            tty=True,
            hostname=self._hostname,
            host_config=self._host_config
        )['Id']

    def _autopull(self):
        """
        Autopulls the docker image of the node, if necessary.
        """
        # Search for image in available images
        for tags in [img['RepoTags'] for img in self._client.images()]:
            if self._image in tags:
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
            'Starting container {}:\n'
            '    Image name: {}\n'
            '    Image id: {}\n'
            '    Image creation date: {}'
            '    Image tags: {}'.format(
                self.container_id,
                self._image,
                image_data.get('Id', '????'),
                image_data.get('Created', '????'),
                ', '.join(image_data.get('RepoTags', []))
            )
        )
        container_data = self._client.inspect_container(
            container=self.container_id
        )
        log.debug(container_data)

    def start(self):
        """
        Start the docker node and configures a netns for it.
        """
        self._client.start(self.container_id)
        self._pid = self._client.inspect_container(
            self.container_id)['State']['Pid']

    def stop(self):
        """
        Request container to stop.
        """
        self._client.stop(self.container_id)
        self._client.wait(self.container_id)
        self._client.remove_container(self.container_id)

    def pause(self):
        """
        Pause the current node.
        """
        for portlbl in self.ports:
            self.set_port_state(portlbl, False)
        self._client.pause(self.container_id)

    def unpause(self):
        """
        Unpause the current node.
        """
        self._client.unpause(self.container_id)
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

        command = 'ip link set dev {iface} {state}'.format(**locals())
        self._docker_exec(command)

    def _docker_exec(self, command):
        """
        Execute a command inside the docker.

        :param str command: The command to execute.
        """
        log.debug(
            '[{}]._docker_exec({}) ::'.format(self.container_id, command)
        )

        response = check_output(shsplit(
            'docker exec {container_id} {command}'.format(
                container_id=self.container_id, command=command.strip()
            )
        )).decode('utf8')

        log.debug(response)
        return response


__all__ = ['DockerNode']
