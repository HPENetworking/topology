==========================
Network Topology Framework
==========================

Network Topology Framework using NML, with support for pytest.


Documentation
=============

    http://topology.rtfd.org/


Changelog
=========

1.2.0
-----

**New**

- Added new API for the topology nodes that allow to set the default shell.
  For example, you may now use ``mynode.default_shell = 'bash'``.
- Documentation for the *Attribute Injection* feature was added.
- Improvements for file matching in attribute injection files. Now, if using
  pytest, all test folders passed as arguments will be used as search paths for
  relative files specified in the attribute injection file. With this, it is no
  longer required to use an absolute path, and this practice becomes deprecated.

**Fixes**

- Fixed a bug in attribute injection when using ``attribute=value`` as node
  identifier that caused all nodes with the attribute to use that value.

1.1.0
-----

**New**

- Added a common ``stateprovider`` decorator to ``topology.libraries.utils``
  that allows to easily inject state to an enode in a Communication library.
- Added a common ``NodeLoader`` class to ``topology.platforms.utils`` that
  allows a Platform Engine to find a load nodes for it's platform.

1.0.1
-----

**Fixes**

- Fixed fatal bug when running a single node topology without ports.
- Fixed new PEP8 checks on the codebase.

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
