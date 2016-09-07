.. toctree::
   :hidden:

   developer
   topology_docker/topology_docker

===================================
Docker Platform Engine for Topology
===================================

.. container:: float-right

   .. image:: _static/images/logo.png

Docker based Platform Engine plugin for the Topology Modular Framework.


Documentation
=============

Element attributes
++++++++++++++++++

Some element attributes are interpreted by this Platform Engine to perform
several actions and setup. For example, the following option are taken into
account in this Platform Engine.

::

   [type=host image="ubuntu:latest"] host1 host2
   [ipv4="192.168.20.20/24"] host1:veth0
   [ipv4="192.168.20.21/24"] host2:veth0
   [category="oobm"] host1:veth1
   [identifier="mainlink" up=False] host1:veth0 -- host2:veth0

Nodes
-----

:type: Type of this node. Node types can be extended using entry points:
 ::

    entry_points={
        'topology_docker_node_10': [
            'host = topology_docker.nodes.host:HostNode',
            'openswitch = topology_docker.nodes.openswitch:OpenSwitchNode'
        ]
    }
:image: Docker image to use for this node. You can run ``docker images`` to
        find the images that are available in your docker installation. To
        specify an image in this attribute, make sure to add the value for the
        ``REPOSITORY`` column and the value for the ``TAG`` column separated by
        a colon, like this: ``image="ubuntu:latest"``.

Ports
-----

:ipv4: IPv4 address to set to this port in the form ``192.168.50.5/24``.
:ipv6: IPv6 address to set to this port in the form ``2001:0db8:0:f101::1/64``.
:up: Bring up (the default) or down this port.
:category: The category this port belongs to. See
           :meth:`topology_docker.node.DockerNode._get_network_config` for more
           information about network categories in a node.

Links
-----

:identifier: Unique idenfier of the link in the topology. It is required to
 explicitly set an identifier to a link to reference it in the
 :meth:`topology_docker.platform.DockerPlatform.unlink` and
 :meth:`topology_docker.platform.DockerPlatform.relink` functions.
:up: Bring up (the default) or down this link
 (implemented as bringing up or down both endpoints).


Engine Node extended interface
++++++++++++++++++++++++++++++

The *Engine Nodes* in this *Platform Engine* have the following additional
methods:

- :meth:`topology_docker.node.DockerNode.pause` and
- :meth:`topology_docker.node.DockerNode.unpause`

This methods allow to pause and resume a node in the topology to test failover,
replication, balancing or for simple management.


Node types provided by default
==============================

This Platform Engine provides two types of nodes by default: *host* and
*switch*.

Host Node Type
++++++++++++++

This is a very simple host that can be used in topologies where there is a need
to simulate a Linux-based host system. This node is based on an Ubuntu 14.04
image (by default) and uses bash for its shell.

It provides the two default network categories (as inherited from DockerNode):
`front_panel` and `oobm`. The first one is used for ports that are going to be
connected to other nodes and the second one is used to connect the node to a
bridge network managed by docker itself (which means it's not explicitly part
of the topology).

Switch Node Type
++++++++++++++++

This is a very simple switch that can be used in topologies where there is a
need to simulate a switch that will just forward packets to the correct port
based on the mac address that's connected to it. This node is based on an
Ubuntu 14.04 image (by default) and uses bash for its shell.

It provides the two default network categories (as inherited from DockerNode):
`front_panel` and `oobm`. The first one is used for ports that are going to be
connected to other nodes and the second one is used to connect the switch to a
bridge network managed by docker itself (which means it's not explicitly part
of the topology).

All the ports in this node type (except the implicit one in the `oobm`
category) are added to a kernel-level bridge named `bridge0` which provides
the switching functionality. Because of the way this type of bridges work, all
interfaces added to it must be set to UP state, which means ports in nodes of
this type will ignore the UP element attribute referenced above (all ports will
be brought UP regardless of it).

Development
===========

- :doc:`Developer Guide. <developer>`
- :doc:`Internal Documentation Reference. <topology_docker/topology_docker>`
- `Project repository. <https://github.com/HPENetworking/topology_docker>`_


License
=======

::

   Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing,
   software distributed under the License is distributed on an
   "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
   KIND, either express or implied.  See the License for the
   specific language governing permissions and limitations
   under the License.
