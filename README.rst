===================================
Docker Platform Engine for Topology
===================================

Docker based Platform Engine plugin for the Network Topology Framework.


Documentation
=============

    http://topology-docker.rtfd.org/


Changelog
=========

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
