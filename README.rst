==================
Topology Framework
==================

Framework for building and testing network topologies, with support for pytest.


Documentation
=============

    https://topology.readthedocs.io/


License
=======

.. code-block:: text

   Copyright (C) 2015-2023 Hewlett Packard Enterprise Development LP

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


Changelog
=========

1.19.0 (2024-10-23)
-------------------

Changes
~~~~~~~

- Add a step before build to resolve the topology graph. This additional step
  allows the user to take decisions before trying to build the topology and
  figuring out it is not possible too late.

- Add "platform" property so users can access the platform instance from the
  topology manager.

1.18.3 (2024-06-25)
-------------------

Fix
~~~

- Move argparse type from 'int' to int.

  In latest version of pytest, the 'int' value as type is
  no longer supported, causing issues when topology is
  started.

1.18.2 (2023-06-15)
-------------------

Fixes
~~~~~
- 'topology' executable was broken and could not be called. Fixed.


1.18.1 (2022-10-31)
-------------------

Fixes
~~~~~
- Using topology as module did not inject attributes appropriately. Now it uses
  the topology file path as top search-path.


1.18.0 (2022-08-39)
-------------------

Changes
~~~~~~~
- Add support for subnode. Subnodes can be specified using the ``node>subnode``
  syntax and they can be nested as well. Ports can be specified for any node
  and links can be specified between any pair of nodes regardless the nesting
  level, for example: ``node>subnode1>subnode2:p1 -- node:p1``.

- Replace NMLExtendedManager by a new TopologyGraph class and other classes
  for Node, Link and Port. TopologyGraph has the same API as the old
  NMLExtendedManager, thus backwards compatibility is preserved.

- Drop support for NML and graphviz plot output which implies these pytest
  plugin flags and CLI arguments now do nothing. Notice they might be removed
  in a future release:

  - --topology-nml-dir
  - --topology-plot-dir
  - --topology-plot-format


1.17.0 (2022-01-25)
-------------------

Changes
~~~~~~~
- pytest flag ``--topology-platform-options`` now uses the ExtendAction to
  allowing extending and overriding options in CLI. [Francisco Mata]


1.16.0 (2021-05-11)
-------------------

New
~~~
- Add pytest option ``--topology-szn-dir``. [Jose Martinez]

  This new option will allow to pass the path of a directory where topologies
  files ``*.szn`` will be defined.


1.15.0 (2021-03-03)
-------------------

New
~~~
- Add pytest option ``--topology-build-retries``. [David Diaz]

  Allow for unstable backends to try topology build more than once.


1.14.0 (2021-01-06)
-------------------

Changes
~~~~~~~
- Call topology rollback on keyboardInterrupt during build. [David Diaz]


1.13.0 (2020-08-05)
-------------------

New
~~~
- Ignore the same paths pytest ignores. [David Diaz]

  When running topology via the pytest plugin, ignore the same paths pytest
  does by using norecursedirs ini option.

  Also move topology plugin configuration to sessionstart as logs on pytest are
  live only after that point.


1.12.0 (2020-06-05)
-------------------

Changes
~~~~~~~
- Use realpath for pytest plugin search paths. [David Diaz]

  Starting on pytest 3.9.2 pytest resolves symbolic links:

  https://github.com/pytest-dev/pytest/pull/4108/

  This causes an incompatibility with the attribute injection feature as the
  paths pytest sees (realpaths) differ from the injected_attr (abspath) found
  on the topology_plugin.


1.11.0 (2020-03-16)
-------------------

Changes
~~~~~~~
- Set a meaningful identifier for NML bilinks. [David Diaz]

  Currently the bilinks ID is the Python instance ID, this commit set it to a
  combination of the port IDs using the same syntax as pyszn:

     ``node0:port0 -- node1:port1``


1.10.0 (2020-01-28)
-------------------

New
~~~
- Platform arguments can now be passed from the CLI and/or the Pytest plugin.
  Use ``--option key=value`` in the CLI and
  ``--topology-platform-option key=value`` in Pytest. Options given using
  this method will be passed as keyword arguments to the platform. Values will
  be "autoparsed" to a Python type using the following order: floats, integers,
  booleans  (yes, no, true, false, case insensitive) and finally any other is
  considered a strings. [Carlos Jenkins & David Diaz]


1.9.15 (2019-11-18)
-------------------

Changes
~~~~~~~
- Removed long ago deprecated module topology.platforms.base [Carlos Jenkins]

    Change imports:

    - topology.platforms.base.BasePlatform => topology.platforms.platform.BasePlatform
    - topology.platforms.base.BaseNode => topology.platforms.node.BaseNode
    - topology.platforms.base.CommonNode => topology.platforms.node.CommonNode

- Update BaseShell __call__ and execute to pass args and kwargs to the wrapped
  call to send_command() (#76) [Sergio Morales]
- Changes to support newer versions of pytest. (#79) [Diego Dompe]
- Drop support for Python 3.4. Minimal version is now 3.5. [Carlos Jenkins]

Fix
~~~
- Topology shells will now use pexpect poll() to support more than 1024 file
  descriptors. This change requires pexpect >= 4.6. [Carlos Jenkins]


1.9.14 (2018-11-21)
-------------------

Changes
~~~~~~~
- Make new testlog func private. [Matthew Hall]


1.9.13 (2018-11-16)
-------------------

New
~~~
- Environment attributes are now passed to the NMLManager. [Javier
  Peralta]
- Add functions for new test specific log. [Matthew Hall]

Changes
~~~~~~~
- Remove unit test of functionalty no longer on topology. [Javier
  Peralta]
- Moving injection to pyszn. [Diego Hurtado]
- Customize term codes regex. [David Diaz]

  Add the ability to customize the terminal regex code for special shells

Fix
~~~
- Pyszn uses correct depedency declaration. [Javier Peralta]
- Minor fixes. [David Diaz]


1.9.12 (2018-06-05)
-------------------

New
~~~
- Add a dynamic timeout option. [Matthew Hall]

  When this option is used expect will be repeated as long as output is
  still being returned.

Changes
~~~~~~~
- Add FORCED_PROMPT to the initial prompt. [Joseph Loaiza]

  The original initial prompt does not match the FORCED_PROMPT, this makes the
  shell to throw a timeout exception when trying to reconnect to a previously
  used shell.

Fix
~~~
- Adding missing release information. [Diego Hurtado]
- Updating to new PEP8 requirements. [Diego Hurtado]


1.9.11 (2017-11-20)
-------------------

Changes
~~~~~~~
- Modify pexpect logger to match actual data stream. [Javier Peralta]

  This change adds a new filehandler that doesn't introduce line changes
  arbitrarily. Also Add some line changes on known places to keep output
  log file readable. With this changes the log file should match
  pexpect's command output stream closer.


1.9.10 (2017-09-06)
-------------------

Changes
~~~~~~~
- Extending connection and disconnection arguments. [Diego Hurtado]

Fix
~~~
- Refactoring _get_connection. [Diego Hurtado]
- Removing support for Python 2.7. [Diego Hurtado]
- Several fixes in the usage of the connection argument. [Diego Hurtado]

  This intentionally breaks compatibility with Python 2.7 since it uses
  syntax introduced in PEP 3102.

- Increase echo sleep 1 second. [Javier Peralta]


1.9.9 (2017-07-26)
------------------

New
~~~
- Adding support for sending control characters. [Diego Hurtado]

Fix
~~~
- Increased delay_after_echo_off a bit. [Javier Peralta]


1.9.8 (2017-06-13)
------------------

Changes
~~~~~~~
- Log python error when plugin load fails. [Javier Peralta]


1.9.7 (2017-05-16)
------------------

Fix
~~~
- Adding a delay after setting echo off. [Javier Peralta]

  Command to set prompt was sometimes too fast and were sent before bash turned
  off echo (stty -echo) resulting in unwanted information being displayed. This
  commit makes sure bash always have time to turn echo off.


1.9.6 (2017-05-03)
------------------

New
~~~
- Adding reason to ``platform_incompatible`` marker.
- Adding timestamps to logs.

Changes
~~~~~~~
- Adding workaround for bug in mock.
- Using ``python3`` as base Python.


1.9.5 (2017-01-06)
------------------

Fix
~~~
- Calling missing ``super``.


1.9.4 (2016-12-13)
------------------

Fix
~~~
- Fixing typo in README.


1.9.3 (2016-12-09)
------------------

Fix
~~~
- Making ``StepLogger`` backwards compatible.


1.9.2 (2016-12-01)
------------------

Fix
~~~
- Fixing broken ``step`` logger.
- Fixing the ``test_id`` marker to make it work with Pytest > 3.0.0.


1.9.1 (2016-11-23)
------------------

Fix
~~~
- Removing fixed dependencies.


1.9.0 (2016-11-10)
------------------

New
~~~
- Adding logging functionality.

Fix
~~~
- Fixing the shells connect process.
- Handling calls to ``decode`` safely.


1.8.1 (2016-09-22)
------------------

Fix
~~~
- Removed internal imports of deprecated modules.


1.8.0 (2016-08-26)
------------------

New
~~~
- A new ServicesAPI for the nodes is now available. This new API allows to
  register and later on fetch information about the services a node provides.
- Greatly improved documentation for the Shell Low Level API introduced in
  1.4.0. Check "The low-level shell API" in User Guide.
- The Low Level Shell API will now be able to log user commands. This new
  feature is backward compatible.

Changes
~~~~~~~
- Module ``topology.platforms.base`` is now deprecated. Please change your
  imports to:

  ::

      topology.platforms.base.BasePlatform => topology.platforms.platform.BasePlatform
      topology.platforms.base.BaseNode     => topology.platforms.node.BaseNode
      topology.platforms.base.CommonNode   => topology.platforms.node.CommonNode


1.7.2 (2016-06-09)
------------------

Changes
~~~~~~~
- Adding ``user`` as an option for ``PExpectShell`` to support shells that use
  this kind of authentication.

Fix
~~~
- Raising the proper exception when a shell connection fails for the user to
  handle it properly.


1.7.1 (2016-05-26)
------------------

Changes
~~~~~~~
- Removing the version requirement of Pexpect since this may cause version
  collisions with other Python packages commonly used with the framework.


1.7.0 (2016-05-26)
------------------

New
~~~
- The reference documentation for the *vtysh*, *ping* and *ip* communication
  libraries has been added to the documentation.
- PExpect shells now support multiple connections. This means that the same
  shell object can now use several ``pexpect`` ``spawn`` objects.

Changes
~~~~~~~
- The documentation for *communication libraries* has been improved a lot with
  specific examples for common use cases added.
- The ``pexpect`` ``spawn`` arguments are now reachable from the initialization
  of a shell object.
- The attribute injection feature is now capable of following symbolic links
  while walking through directory paths.
- The version of all dependencies has been fixed. This is to avoid unexpected
  code breaks when a bug is introduced in one of them.

Fix
~~~
- The base node class ``BaseNode`` now includes a ``ports`` attribute. This has
  been used by all platform engine nodes so far, but was missing in their base
  class.
- A missing history file does not raise an error whene executing ``topology``,
  but is just logged as an error.
- A few CSS and other theme issues have been fixed.


1.6.0 (2016-03-21)
------------------

Changes
~~~~~~~
- When expanding the search path for attribute injection all hidden folders
  (starting with '.') will now be ignored.
- When processing files that matched the search path for attribute injection
  all files that have ill formed / unparseable SZN strings will be logged as
  error and skipped instead of raising an exception.
- When processing files that matched the search path for attribute injection
  all ``.py``'s that doesn't possess a ``TOPOLOGY`` variable will now be warned
  and skipped instead of raising an exception.

Fix
~~~
- Fixed attribute injection crashing when a SZN file is in the node expansion
  search path.
- Fixed rollback routine not being triggered when an non ``Exception`` subclass
  is raised.


1.5.0 (2016-03-02)
------------------

New
~~~
- New ``topology.platforms.shell.PExpectBashShell`` class that allows to easily
  setup shells that uses bash.

Fix
~~~
- Fixed small identation bug that caused the function ``get_shell()`` in the
  node API to return always ``None``.


1.4.0 (2016-03-01)
------------------

New
~~~
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

Changes
~~~~~~~
- The shell used to execute a command will now be logged.


1.3.0 (2016-02-17)
------------------

Changes
~~~~~~~
- Attribute injection will now try to match files on any subfolder of the
  search paths and not only on the search paths themselves.

Fix
~~~
- Fixed critical bug in injection attribute not considering matches in some
  cases.


1.2.0 (2016-02-13)
------------------

New
~~~
- Added new API for the topology nodes that allow to set the default shell.
  For example, you may now use ``mynode.default_shell = 'bash'``.
- Documentation for the *Attribute Injection* feature was added.
- Improvements for file matching in attribute injection files. Now, if using
  pytest, all test folders passed as arguments will be used as search paths for
  relative files specified in the attribute injection file. With this, it is no
  longer required to use an absolute path, and this practice becomes deprecated.

Fix
~~~
- Fixed a bug in attribute injection when using ``attribute=value`` as node
  identifier that caused all nodes with the attribute to use that value.


1.1.0 (2016-01-26)
------------------

New
~~~
- Added a common ``stateprovider`` decorator to ``topology.libraries.utils``
  that allows to easily inject state to an enode in a Communication library.
- Added a common ``NodeLoader`` class to ``topology.platforms.utils`` that
  allows a Platform Engine to find a load nodes for it's platform.


1.0.1 (2016-01-22)
------------------

Fix
~~~
- Fixed fatal bug when running a single node topology without ports.
- Fixed new PEP8 checks on the codebase.


1.0.0 (2016-01-05)
------------------

New
~~~
- Initial public release.
