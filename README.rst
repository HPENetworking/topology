==========================
Network Topology Framework
==========================

Network Topology Framework using NML, with support for pytest.


Documentation
=============

    http://topology.rtfd.org/


Changelog
=========

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
