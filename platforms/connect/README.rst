================
Topology Connect
================

Topology Connect its a plugin (called a Platform Engine) for the Topology
Modular Framework that allows to connect to and interact with an existing
physical topology using SSH or Telnet.

This is particularly useful to perform tests on small, hardwired, already-built
topologies inside a lab.

The main use case is to specify IPs of the devices using a Attribute Injection
File (AIF) or by specifying the IPs to connect to in the topology description
file itself (SZN file).


Documentation
=============

    http://topology.readthedocs.io/


Changelog
=========

0.4.0
-----

**Changes**

- Updated the base CommonConnectNode to support the Services API introduced in
  Topology Modular Framework 1.8.
- Removed the ``hostname`` attribute in the base ConnectNode so it doesn't
  clash with topology_docker ``hostname`` attribute. Same name, but different
  purpose. To connect to a node specify the ``fqdn`` attribute in the SZN or
  using attribute injection.


0.3.0
-----

**Fixes**

- Fixed issue #4 where the SshMixin created an attribute name collision with
  parent classes.

**Changes**

- Removed placeholder documentation as the new Topology Modular Framework
  website will hold all documentation for the project and official plugins.


0.2.0
-----

- First beta version.


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
