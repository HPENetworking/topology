===================================
Docker Platform Engine for Topology
===================================

Docker based Platform Engine plugin for the Network Topology Framework.


Documentation
=============

    http://topology-docker.rtfd.org/


Changelog
=========

1.5.0
-----

**Changes**

The only change in this version is the transference of all specialized support
nodes previously included with this platform engine into their own repositories.
This change seeks to improve maintainability of the platform engine, separation
of the support nodes issues, requirements and enhancements from those of the
platform and, finally, endorse shared ownership of the nodes.

The new home for those support nodes are:

:OpenSwitch support node:
 https://github.com/HPENetworking/topology_docker_openswitch

:Open vSwitch support node:
 https://github.com/HPENetworking/topology_docker_openvswitch

:P4Switch support node:
 https://github.com/HPENetworking/topology_docker_p4switch

:Ryu Controller support node:
 https://github.com/HPENetworking/topology_docker_ryu


1.4.0
-----

**New**

- The ``binds`` attribute can now be injected and extended by users. If you
  require to add a new bind directory to a node you may now specify the
  attribute ``binds`` (and thus, also use attribute injection) separating the
  pair of binded directories with a ``;``. For example::

      /host/a:/container/a;/host/b:/container/b

- OpenSwitch support node will now notify the container when the setup of the
  interfaces is done. This fixes many potential race conditions on container
  initialization. To be able to use this new feature an OpenSwitch image of a
  date greater than March 4 2016 is required.

**Changes**

- Set ``topology`` minimal version to ``1.5.0``.
- Internal ``docker exec`` shell layer migrated to Topology's new shell API,
  available since 1.4.0 and improved in 1.5.0.

**Fixes**

- OpenSwitch support node will now ignore the ``bonding_masters`` interface
  when creating setting up the ports.
- Fixed a race condition in OpenSwitch support node caused by a slower than
  normal db schema setup in ovsdb. This race conditions caused an ``IndexError``
  when setting up the image, causing the topology build to rollback.

1.3.0
-----

**Changes**

- Node's/Container's hostname can now be set using the ``hostname`` attribute
  in the SZN description. OpenSwitch will always enforce the ``switch``
  hostname for all nodes of this type.
- Docker-py's will now use the server's API version, instead of the latest.
  With this it will no longer required to update the Docker daemon to run
  topology tests.
- Set ``topology`` minimal version to ``1.2.0``.

1.2.0
-----

**Changes**

- Refactored node loading logic to use ``topology.platforms.utils.NodeLoader``
  instead.

1.1.0
-----

**New**

- Added Dockerfiles for Ryu and P4.

**Changes**

- The Open vSwitch node will now check that the ``openvswitch`` kernel module
  is loaded. It is supposed to work in user space, but we discovered many race
  conditions without the kernel module.
  Check the documentation of the ``openvswitch`` node for more information.

**Fixes**

- Improved openswitch's vtysh prompt regular expression to avoid false
  positives matches.
- Fixed a bug on shell management that caused the echo of the command to be
  included in the output, and thus interpreted as failed.

1.0.0
-----

- Initial public release.


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
