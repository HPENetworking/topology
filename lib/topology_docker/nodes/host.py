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
Simple host Topology Docker Node using Ubuntu.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from topology_docker.node import DockerNode
from topology_docker.shell import DockerBashShell


class HostNode(DockerNode):
    """
    Simple host node for the Topology Docker platform engine.

    This base host loads an ubuntu image (by default) and has bash as the
    default shell.

    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(self, identifier, image='ubuntu:14.04', **kwargs):

        super(HostNode, self).__init__(identifier, image=image, **kwargs)
        self._shells['bash'] = DockerBashShell(
            self.container_id, 'bash'
        )


__all__ = ['HostNode']
