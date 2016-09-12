==========================
Topology Modular Framework
==========================

.. image:: https://travis-ci.org/ocelotl/ocelotl_topology.svg?branch=master
   :target: https://travis-ci.org/ocelotl/ocelotl_topology

Advanced modular framework for building and testing network topologies and
Software.


Documentation
=============

    http://topology.rtfd.io/


Changelog
=========

1.8.0
-----

**New**

- A new ServicesAPI for the nodes is now available. This new API allows to
  register and later on fetch information about the services a node provides.
- Greatly improved documentation for the Shell Low Level API introduced in
  1.4.0. Check "The low-level shell API" in User Guide.
- The Low Level Shell API will now be able to log user commands. This new
  feature is backward compatible.

**Changes**

- Module ``topology.platforms.base`` is now deprecated. Please change your
  imports to:

  ::

      topology.platforms.base.BasePlatform => topology.platforms.platform.BasePlatform
      topology.platforms.base.BaseNode     => topology.platforms.node.BaseNode
      topology.platforms.base.CommonNode   => topology.platforms.node.CommonNode

1.7.2
-----

**Changes**

- Adding ``user`` as an option for ``PExpectShell`` to support shells that use
  this kind of authentication.

**Fixes**

- Raising the proper exception when a shell connection fails for the user to
  handle it properly.

1.7.1
-----

**Changes**

- Removing the version requirement of Pexpect since this may cause version
  collisions with other Python packages commonly used with the framework.

1.7.0
-----

**Changes**

- The documentation for *communication libraries* has been improved a lot with
  specific examples for common use cases added.
- The ``pexpect`` ``spawn`` arguments are now reachable from the initialization
  of a shell object.
- The attribute injection feature is now capable of following symbolic links
  while walking through directory paths.
- The version of all dependencies has been fixed. This is to avoid unexpected
  code breaks when a bug is introduced in one of them.

**New**

- The reference documentation for the *vtysh*, *ping* and *ip* communication
  libraries has been added to the documentation.
- PExpect shells now support multiple connections. This means that the same
  shell object can now use several ``pexpect`` ``spawn`` objects.

**Fixes**

- The base node class ``BaseNode`` now includes a ``ports`` attribute. This has
  been used by all platform engine nodes so far, but was missing in their base
  class.
- A missing history file does not raise an error whene executing ``topology``,
  but is just logged as an error.
- A few CSS and other theme issues have been fixed.

1.6.0
-----

**Changes**

- When expanding the search path for attribute injection all hidden folders
  (starting with '.') will now be ignored.
- When processing files that matched the search path for attribute injection
  all files that have ill formed / unparseable SZN strings will be logged as
  error and skipped instead of raising an exception.
- When processing files that matched the search path for attribute injection
  all ``.py``'s that doesn't possess a ``TOPOLOGY`` variable will now be warned
  and skipped instead of raising an exception.

**Fixes**

- Fixed attribute injection crashing when a SZN file is in the node expansion
  search path.
- Fixed rollback routine not being triggered when an non ``Exception`` subclass
  is raised.

1.5.0
-----

**New**

- New ``topology.platforms.shell.PExpectBashShell`` class that allows to easily
  setup shells that uses bash.

**Fixes**

- Fixed small identation bug that caused the function ``get_shell()`` in the
  node API to return always ``None``.

1.4.0
-----

**Changes**

- The shell used to execute a command will now be logged.

**New**

- New low level shell API that allows to define a common behavior for all low
  level shell manipulation. This API is implemented by the
  ``topology.platforms.shell`` module.
- Two new high level API methods for accesing the low level shell API::

      myshell = mynode.get_shell('python')
      response = myshell.execute('1 + 1')

  Or using a context manager::

      with mynode.use_shell('python') as python:
          # This context manager sets the default shell to 'python'
          mynode('from os import getcwd')
          cwd = mynode('print(getcwd())')

          # Access to the low-level shell API
          python.send_command('foo = (', matches=['... '])

1.3.0
-----

**Changes**

- Attribute injection will now try to match files on any subfolder of the
  search paths and not only on the search paths themselves.

**Fixes**

- Fixed critical bug in injection attribute not considering matches in some
  cases.

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
