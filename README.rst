==========================
Topology Modular Framework
==========================

.. image:: https://travis-ci.org/HPENetworking/topology.svg?branch=master
   :target: https://travis-ci.org/HPENetworking/topology

Advanced modular framework for building and testing network topologies and
Software.


Documentation
=============

    http://topology.rtfd.io/

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

Changelog
=========

Changelog
=========


1.9.12 (2018-06-05)
-------------------

Changes
~~~~~~~
- Bumping version to 1.9.12. [Diego Antonio Hurtado Pimentel]
- Add FORCED_PROMPT to the initial prompt. [Joseph Loaiza]

  The original initial prompt does not match the FORCED_PROMPT, this makes the shell to throw a timeout exception when trying to reconnect to a previously used shell.

Fix
~~~
- Adding missing release information. [Diego Antonio Hurtado Pimentel]
- Updating to new PEP8 requirements. [Diego Antonio Hurtado Pimentel]

Other
~~~~~
- Add a dynamic timeout option. [Matthew Hall]

  When this option is used expect will be repeated as long as output is
  still being returned.


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
- Extending connection and disconnection arguments. [Diego Antonio
  Hurtado Pimentel]

Fix
~~~
- Refactoring _get_connection. [Diego Antonio Hurtado Pimentel]
- Removing support for Python 2.7. [Diego Antonio Hurtado Pimentel]
- Several fixes in the usage of the connection argument. [Diego Antonio
  Hurtado Pimentel]

  This intentionally breaks compatibility with Python 2.7 since it uses
  syntax introduced in PEP 3102.
- Increase echo sleep 1 second. [Javier Peralta]


1.9.9 (2017-07-26)
------------------

New
~~~
- Adding support for sending control characters. [Diego Antonio Hurtado
  Pimentel]

Changes
~~~~~~~
- Bumping version to 1.9.9. [Javier Peralta]

Fix
~~~
- Increased delay_after_echo_off a bit. [Javier Peralta]


1.9.8 (2017-06-13)
------------------

Changes
~~~~~~~
- Refactoring the changelog. [Diego Antonio Hurtado Pimentel]
- Log python error when plugin load fails. [Javier Peralta]


1.9.7 (2017-05-16)
------------------

Fix
~~~
- Add some sleeps to allow bash to turn echo off. [Javier Peralta]

  Command to set prompt was sometimes too fast and were sent
  before bash turned off echo (stty -echo) resulting in
  unwanted information being displayed. This commit makes
  sure bash always have time to turn echo off.


1.9.6 (2017-05-03)
------------------

New
~~~
- Add reason to platform_incompatible marker. [David Diaz]

Changes
~~~~~~~
- Adding timestamps to logs. [Diego Antonio Hurtado Pimentel]
- Tox.ini now uses python3 as base. [Javier Peralta]
- Add workaround for bug in mock. [Javier Peralta]


1.9.5 (2017-01-06)
------------------

Fix
~~~
- Calling super in init. [Diego Antonio Hurtado Pimentel]


1.9.4 (2016-12-13)
------------------

Fix
~~~
- Fixing typo in README. [Diego Antonio Hurtado Pimentel]


1.9.3 (2016-12-09)
------------------

Fix
~~~
- Keeping StepLogger backwards compatible. [Diego Antonio Hurtado
  Pimentel]


1.9.2 (2016-12-01)
------------------

Changes
~~~~~~~
- Refactored step logger to match new logging architecture. [Carlos
  Jenkins]

Fix
~~~
- Making test_id marker work with the new Pytest. [Diego Antonio Hurtado
  Pimentel]
- Calling right class. [Diego Antonio Hurtado Pimentel]
- Added missing registration of the loggers. [Carlos Jenkins]
- Minor fixes. [Diego Antonio Hurtado Pimentel]
- Adding logger for step. [Diego Antonio Hurtado Pimentel]


1.9.1 (2016-11-23)
------------------

Fix
~~~
- Removing fixed dependencies. [Diego Antonio Hurtado Pimentel]


1.9.0 (2016-11-10)
------------------

New
~~~
- Documenting --topology-log-dir. [Diego Antonio Hurtado Pimentel]
- New framework wide logging subsystem. [Diego Antonio Hurtado Pimentel]

Fix
~~~
- Handling decode errors safely. [Diego Antonio Hurtado Pimentel]
- Fixing wrong usage of _initial_command. [Diego Antonio Hurtado
  Pimentel]
- Setting default errors to ignore. [Diego Antonio Hurtado Pimentel]

  The idea of this is to avoid UnicodeDecodeErrors when a undecodeable
  character shows up in the output that is to be kept by the Pexpect
  logger by default but to also allow for strict checking if needed.
- Fixing LEVELS constant. [Diego Antonio Hurtado Pimentel]
- Fixing log_dir and file_formatter setting. [Diego Antonio Hurtado
  Pimentel]


1.8.1 (2016-09-22)
------------------

New
~~~
- Adding CI spec file. [Diego Antonio Hurtado Pimentel]

Changes
~~~~~~~
- Bumping version number to 1.8.1. [Carlos Miguel Jenkins Perez]

Fix
~~~
- Setting right image URL. [Diego Antonio Hurtado Pimentel]
- Changed deprecated module import. [Carlos Miguel Jenkins Perez]


1.8.0 (2016-08-26)
------------------

New
~~~
- Added a new Services API to manage services running in a node. [Carlos
  Miguel Jenkins Perez]
- Adding support for low-level shell API logging. [Diego Antonio Hurtado
  Pimentel]

  Conflicts:
  	lib/topology/platforms/base.py
- Adding user documentation for shell API. [Diego Antonio Hurtado
  Pimentel]

Changes
~~~~~~~
- Bumping version number to 1.8.0. [Carlos Miguel Jenkins Perez]
- Module ``topology.platforms.base`` is now deprecated. Please change
  your imports to: [Carlos Miguel Jenkins Perez]

  ::

      topology.platforms.base.BasePlatform => topology.platforms.platform.BasePlatform
      topology.platforms.base.BaseNode     => topology.platforms.node.BaseNode
      topology.platforms.base.CommonNode   => topology.platforms.node.CommonNode

Fix
~~~
- Setting encoding in response logger. [Diego Antonio Hurtado Pimentel]
- Removing prints from send_command. [Diego Antonio Hurtado Pimentel]
- Adding missing methods. [Diego Antonio Hurtado Pimentel]
- Minor documentation fixes, name changes, etc. [Carlos Miguel Jenkins
  Perez]
- Minor fixes in documentation and upgrading the AutoAPI plugin for
  better output format. [Carlos Miguel Jenkins Perez]


1.7.2 (2016-06-09)
------------------

New
~~~
- Adding user matching in PExpectShell. [Diego Antonio Hurtado Pimentel]

Changes
~~~~~~~
- Bumping version number to 1.7.2. [Diego Antonio Hurtado Pimentel]

Fix
~~~
- Adding a missing raise. [Diego Antonio Hurtado Pimentel]


1.7.1 (2016-05-26)
------------------

Changes
~~~~~~~
- Bumping version number to 1.7.1. [Diego Antonio Hurtado Pimentel]

Fix
~~~
- Removing version requirement for pexpect. [Diego Antonio Hurtado
  Pimentel]


1.7.0 (2016-05-26)
------------------

New
~~~
- Adding support for multiple connections. [Diego Antonio Hurtado
  Pimentel]

  So far, Topology shells have only supported one connection per
  shell. This adds multiple-connection functionality to the basic
  shell classes provided.
- Adding reference documentation for IP and Ping libraries. [Carlos
  Miguel Jenkins Perez]
- Added the reference documentation for the vtysh communication library.
  [Carlos Miguel Jenkins Perez]
- Improved documentation a lot. Really. Still a lot to do tought.
  [Carlos Miguel Jenkins Perez]

Changes
~~~~~~~
- Bumping version number to 1.7.0. [Diego Antonio Hurtado Pimentel]
- Exposing Pexpect spawn constructor arguments. [Diego Antonio Hurtado
  Pimentel]
- For documentation, better grab from master. [Carlos Miguel Jenkins
  Perez]
- Making the new theme official. [Carlos Miguel Jenkins Perez]
- Porting some key legibility concepts of the Hauntr theme into the
  Guzzle theme. [Carlos Miguel Jenkins Perez]
- Improved documentation about communication libraries in the plugin
  developer guide. [Carlos Miguel Jenkins Perez]

Fix
~~~
- Fixing the version of all dependencies. [Diego Antonio Hurtado
  Pimentel]
- Allow walk to iterate through symbolic links. [fonsecamau]
- Minor documentation fixes. [Carlos Miguel Jenkins Perez]
- Fixing some minor references to code classes. [Carlos Miguel Jenkins
  Perez]
- Other theme minor whitespace and style fixes. [Carlos Miguel Jenkins
  Perez]
- Fixed some CSS issues with new theme. [Carlos Miguel Jenkins Perez]
- Missing history file will no longer show an ERROR when loading the
  topology executable. [Carlos Miguel Jenkins Perez]

  This fixes #14.
- Added missing public interface attribute in the BaseNode API. [Carlos
  Miguel Jenkins Perez]


1.6.0 (2016-03-21)
------------------

New
~~~
- Included image that describes the components of the framework. [Carlos
  Miguel Jenkins Perez]

Changes
~~~~~~~
- Bumping version number to 1.6.0 for minor release. [Carlos Miguel
  Jenkins Perez]

  1.6.0: The "Hard rock attribute injection" release.

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
- When expanding the search path for attribute injection all hidden
  folders (starting with '.') will now be ignored. [Carlos Miguel
  Jenkins Perez]
- When processing files that matched the search path for attribute
  injection all files that have ill formed / unparseable SZN strings
  will be logged as error and skipped instead of raising an error.
  [Carlos Miguel Jenkins Perez]
- When processing files that matched the search path for attribute
  injection all .py that doesn't possess a TOPOLOGY will now be warned
  and skipped instead of raising an error. [Carlos Miguel Jenkins Perez]

Fix
~~~
- Fixed attribute injection when a SZN file is in the node expansion
  search path. [Carlos Miguel Jenkins Perez]
- Fixed rollback routine not being triggered when an non Exception
  subclass is raised. [Carlos Miguel Jenkins Perez]
- Minor spelling fix. [Carlos Miguel Jenkins Perez]


1.5.0 (2016-03-02)
------------------

New
~~~
- New PExpectBashShell class that allows to easily setup shells that
  uses bash. [Carlos Miguel Jenkins Perez]

Changes
~~~~~~~
- Bumping version number to 1.5.0 for minor release. [Carlos Miguel
  Jenkins Perez]

Fix
~~~
- Fixed small identation bug that caused the function ``get_shell()`` in
  the node API to return always None. [Carlos Miguel Jenkins Perez]


1.4.0 (2016-03-01)
------------------

New
~~~
- Documenting the new shell API. [Diego Antonio Hurtado Pimentel]
- New Node API call use_shell() that allows to use a different default
  shell in a context. [Carlos Miguel Jenkins Perez]
- New Node API call get_shell() that alows to access the low-level Shell
  API. [Carlos Miguel Jenkins Perez]
- New low-level Shell API. [Carlos Miguel Jenkins Perez]

Changes
~~~~~~~
- Bumping version number to 1.4.0 for minor release. [Carlos Miguel
  Jenkins Perez]

Fix
~~~
- Logging the command in the debug platform in the same way as in
  CommonNode. [Carlos Miguel Jenkins Perez]
- Fixed unbuild when using exit() in the topology executable in
  interactive mode. [Carlos Miguel Jenkins Perez]

  This fixes issue #11.
- Fixing shell command prefixing. [Diego Antonio Hurtado Pimentel]
- Log shell used in send_commands calls. [Carlos Miguel Jenkins Perez]

  This closes issue #5.


1.3.0 (2016-02-17)
------------------

Changes
~~~~~~~
- Bumping version number to 1.3.0 for minor release. [Carlos Miguel
  Jenkins Perez]
- Attribute injection will now try to match files on any subfolder of
  the search paths and not only on the search paths themselves. [Carlos
  Miguel Jenkins Perez]
- Updated injection test to reflect the use of search paths. [Carlos
  Miguel Jenkins Perez]

Fix
~~~
- Fixed critical bug in injection attribute not considering matches in
  some cases. [Carlos Miguel Jenkins Perez]


1.2.0 (2016-02-13)
------------------

New
~~~
- Added documentation for attribute injection feature. [Carlos Miguel
  Jenkins Perez]
- New API to BaseNode to allow to change the default shell. [Carlos
  Miguel Jenkins Perez]

Changes
~~~~~~~
- Bumping version number to 1.2.0 for minor release. [Carlos Miguel
  Jenkins Perez]
- Improves file matching for attribute injection using pytest testing
  directories arguments as search paths. [Carlos Miguel Jenkins Perez]

  With this change the attribute injection file can specify relative wildcards and relative paths from the pytest testing directories arguments.

Fix
~~~
- Fixing bad matching for attribute=value criteria. [Diego Antonio
  Hurtado Pimentel]


1.1.0 (2016-01-26)
------------------

New
~~~
- Added a helper to load nodes for a engine platform. [Carlos Miguel
  Jenkins Perez]
- Added the stateprovider decorator to the core. [Carlos Miguel Jenkins
  Perez]

  The stateprovider decorator allows to easily implement the common
  pattern of injecting the state of the library into the engine node.

Changes
~~~~~~~
- Bumping version number to 1.1.0 for minor release. [Carlos Miguel
  Jenkins Perez]


1.0.1 (2016-01-22)
------------------

Changes
~~~~~~~
- Bumping version to 1.0.1 and adding changelog. [Carlos Miguel Jenkins
  Perez]

Fix
~~~
- Fixes to consider new pep8 requirements. [Diego Antonio Hurtado
  Pimentel]
- Fixed URL of the repository now that it moved. [Carlos Miguel Jenkins
  Perez]
- Removing reference to mininet and adding the new URL for
  topology_docker. [Carlos Miguel Jenkins Perez]
- Fix topology fails when node has no links (#16) [David Diaz]


1.0.0 (2016-01-05)
------------------

New
~~~
- Added enable/disable abstract methods to BaseNode. [Carlos Miguel
  Jenkins Perez]

  This allow Platform Engines to specify this behaviour in a framework-wide standard way.

  This address issue #4.
- Added support for injecting attributes when using the topology script.
  [Carlos Miguel Jenkins Perez]
- Setting plugin to handle attribute injection. [Diego Antonio Hurtado
  Pimentel]
- Adding test for attribute injection. [Diego Antonio Hurtado Pimentel]
- Handling attribute injection. [Diego Antonio Hurtado Pimentel]
- Adding parser for attribute injection. [Diego Antonio Hurtado
  Pimentel]
- Added the new step fixture to log steps in tests. [Carlos Miguel
  Jenkins Perez]
- Added the feature to notify the enodes of their port mapping. [Carlos
  Miguel Jenkins Perez]
- Added the unlink and relink call to topology manager and to the
  platform specification. [Carlos Miguel Jenkins Perez]
- Added testing for the autoport feature and modified parser to try to
  interpret some basic datatypes in attributes. [Carlos Miguel Jenkins
  Perez]
- Implemented the autoport feature. [Carlos Miguel Jenkins Perez]
- Implemented the port spec load in topology manager load() function now
  that the parser can deal with port attributes. [Carlos Miguel Jenkins
  Perez]
- Added some architecture documentation. [Carlos Miguel Jenkins Perez]
- Improved user documentation a lot. [Carlos Miguel Jenkins Perez]
- Implemented the missing plot and nml export features in the topology
  executable. [Carlos Miguel Jenkins Perez]
- Implemented a new parser based on pyparsing that supports port
  attributes. [Carlos Miguel Jenkins Perez]
- Added a new incompatible marker to mark specific test as incompatible
  with a platform engine. [Carlos Miguel Jenkins Perez]
- Added a new built-in communication library for asserts. [Carlos Miguel
  Jenkins Perez]
- Added the feature to extra the TOPOLOGY variable from Python files for
  the topology executable. [Carlos Miguel Jenkins Perez]
- Added a very basic documentation for the topology executable. [Carlos
  Miguel Jenkins Perez]
- Added an option to hide commands during build to the topology
  executable. [Carlos Miguel Jenkins Perez]
- Implemented the topology executable with interactive mode. [Carlos
  Miguel Jenkins Perez]
- Added cookiecutter template files for a executable. [Carlos Miguel
  Jenkins Perez]
- Added the rollback hook to the base platform class. [Carlos Miguel
  Jenkins Perez]
- Implemented echo/silent feature in CommonNode.send_command() to print
  command and result. [Carlos Miguel Jenkins Perez]
- Passing port number as metadata. [Carlos Miguel Jenkins Perez]
- Checking that node identifiers are valid. [Carlos Miguel Jenkins
  Perez]
- Implemented the load() method to load the dictionary topology
  description. [Carlos Miguel Jenkins Perez]
- Added a new output export NML XML for topologies found. [Carlos Miguel
  Jenkins Perez]
- Added a doctest to the manager module to test the workflow. [Carlos
  Miguel Jenkins Perez]
- Added support for test_id marker and changed name and semantics of the
  --topology-plot flag to now be able to specify the folder. [Carlos
  Miguel Jenkins Perez]
- Added the auto-plot feature for the pytest plugin. [Carlos Miguel
  Jenkins Perez]
- Finished implementing and tested pytest plugin. [Carlos Miguel Jenkins
  Perez]
- Added support for positional arguments to be passed from tox to
  pytest. [Carlos Miguel Jenkins Perez]

  For example:

      tox -e py27 -- --traceconfig

  Will pass the --traceconfig to pytest.
- Added support for communication libraries for included engine
  platforms enodes. [Carlos Miguel Jenkins Perez]
- Added manager for communication libraries. [Carlos Miguel Jenkins
  Perez]
- Added a new Debug Engine Paltform to test our codebase for Python 3.4
  without requiring Mininet (as it doesn't support Python 3) [Carlos
  Miguel Jenkins Perez]
- Added a test to test all the build workflow of a TopologyManager.
  [Carlos Miguel Jenkins Perez]
- Extended documentation for plugin implementation, in particular for
  communication libraries. [Carlos Miguel Jenkins Perez]

  Also extended the BaseNode interface to support the documentation.
- Implemented txtmeta parser in TopologyManager. [Carlos Miguel Jenkins
  Perez]
- Add logic to add_biport on mininet plugin. [David Diaz]

  The port is stored inside the plugin but it is not propagated to
  mininet. When a link is made, the interface will have the correct
  port number in its name.
- Added a lot of missing documentation. [Carlos Miguel Jenkins Perez]
- Added support for Graphviz graphs in Sphinx documentation. [Carlos
  Miguel Jenkins Perez]
- Added new documentation for engine platforms plugin developers.
  [Carlos Miguel Jenkins Perez]
- Added support for plantUML in Sphinx documentation. [Carlos Miguel
  Jenkins Perez]
- Implement send command for mininet plugin. [David Diaz]

  Also add a related test
- Implement mininet plugin, add nodes and links. [David Diaz]

  Also adds a py.test related
- Add mininet and pynml to requirements. [David Diaz]
- Initial version of the topology dot-like syntax parser. [Carlos Miguel
  Jenkins Perez]
- Added base pytest plugin for topology. [Carlos Miguel Jenkins Perez]
- First example of a test using the topology module. [Carlos Miguel
  Jenkins Perez]
- Initial base code and draft on the implementation. [Carlos Miguel
  Jenkins Perez]
- Initial repository layout. [Carlos Miguel Jenkins Perez]

Changes
~~~~~~~
- Changed URLs, version number and requirements for public release.
  [Carlos Miguel Jenkins Perez]
- Added timestamp in ISO 8601 format to all commands logging. [Carlos
  Miguel Jenkins Perez]

  This address issue #8.
- Update doc to reflect that classes can be defined on libraries. [David
  Diaz]
- Libraries are now namespaced. [Carlos Miguel Jenkins Perez]
- Change assert library name as it is a reserved word. [David Diaz]
- Rewrote from scratch the communication libraries mechanism for a
  better approach. [Carlos Miguel Jenkins Perez]
- Removing autoport and port_number metadata from ports as with the new
  label metadata they are not required. [Carlos Miguel Jenkins Perez]
- Added registration of the engine port number to a topology internal
  structure. [Carlos Miguel Jenkins Perez]
- Removed the autoport feature from the core framework and changed the
  approach to a labeled port that must be handled by the platform
  engine. [Carlos Miguel Jenkins Perez]
- More crazy stuffs with higly cohesive grouping... [Carlos Miguel
  Jenkins Perez]
- Crazy stuffs grouping highly cohesive options... [Carlos Miguel
  Jenkins Perez]
- Refactored the platform entry point loader to lazy load the platform
  and thus avoiding importing all platforms with just the import of the
  module. [Carlos Miguel Jenkins Perez]
- Stripping down the mininet platform engine from the core. [Carlos
  Miguel Jenkins Perez]
- Refactored the parser module into it's own. [Carlos Miguel Jenkins
  Perez]
- Resync repository with template. [Carlos Miguel Jenkins Perez]
- Changed the way Tox works: [Carlos Miguel Jenkins Perez]

  - Python 3.4 is now the default for everything.
  - The build is now always done in the temporal directory by default.
  - Removed tox from requirements.dev.txt as it is not a virtualenv dependency.
  - The doctest discovery now works.
- Changed the default platform to be dependent on the interpreter
  version. [Carlos Miguel Jenkins Perez]
- Improved internal documentation for the pytest topology plugin.
  [Carlos Miguel Jenkins Perez]
- Fixed error reporting for the parser and the plugin. [Carlos Miguel
  Jenkins Perez]
- Better changed that when running in Python3 do not skip the plugin
  test, just ensure a compatible engine, overriding the command line
  option. [Carlos Miguel Jenkins Perez]
- Refactored common logic into a CommonNode class. [Carlos Miguel
  Jenkins Perez]
- Resynced the repository with it's cookiecutter template and thus we
  now build the reference documentation with AutoAPI. [Carlos Miguel
  Jenkins Perez]
- Add installation instructions related to mininet on documentation.
  [David Diaz]
- Fixed mockup nodes using name as identifier and added missing
  identifier attribute to BaseNode. [Carlos Miguel Jenkins Perez]
- Changed the shells available to the Mininet Engine nodes and added a
  placeholder for future communication libraries. [Carlos Miguel Jenkins
  Perez]
- Added support for dictmeta format in TOPOLOGY variable to the pytest
  plugin. [Carlos Miguel Jenkins Perez]
- Change parameter name on node metadata from variant to type. [David
  Diaz]
- Add internal documentation to mininet plugin. [David Diaz]
- Remove nml manager instance on baseplatform as they are on the
  constructor. [David Diaz]
- Added general module documentation. [Diego Antonio Hurtado Pimentel]
- Updated template for documentation rendering. [Carlos Miguel Jenkins
  Perez]
- Moves NMLManager to pynml module. [David Diaz]

Fix
~~~
- Passing the correct manager to the topology script namespace. The
  correct manager is the one that allows to unlink and relink. [Carlos
  Miguel Jenkins Perez]
- Removed deprecated attribute. [Carlos Miguel Jenkins Perez]
- Fixed formatting of the step logger. [Carlos Miguel Jenkins Perez]
- Fixed return value of the step fixture. [Carlos Miguel Jenkins Perez]
- Changing shebang of the topology script to Python3. [Carlos Miguel
  Jenkins Perez]
- Fixing pytest assert relaunching the command when the asserts fails
  and a possible non failure on second assert. [Carlos Miguel Jenkins
  Perez]
- Fixed bad attribute name. [Carlos Miguel Jenkins Perez]
- Updated the documentation in the plugin dev guide to reflect change in
  the workflow. [Carlos Miguel Jenkins Perez]
- Fixed bad documentation docstring. [Carlos Miguel Jenkins Perez]
- Unifying the jargon. [Carlos Miguel Jenkins Perez]
- Minor documentation fixes. [Carlos Miguel Jenkins Perez]
- Fixed typos and unclear documentation. [Carlos Miguel Jenkins Perez]
- Fixed non-responsive plantuml diagram. [Carlos Miguel Jenkins Perez]
- Printing the command previous its call to log adequately for failures.
  [Carlos Miguel Jenkins Perez]
- Fixed bug in the way communication libraries functions are called.
  [Carlos Miguel Jenkins Perez]
- Fixed a couple of bugs. One related to libraries loading and the other
  to error messasge printing. [Carlos Miguel Jenkins Perez]
- Fixed testing of the new feature. [Carlos Miguel Jenkins Perez]
- Add missing instructions to install graphviz. [Carlos Miguel Jenkins
  Perez]
- Fixing stupid ups. [Carlos Miguel Jenkins Perez]
- Fixed the test_id mark issue when interacting with skipif. [Carlos
  Miguel Jenkins Perez]
- Minor style fixes. [Carlos Miguel Jenkins Perez]
- Check if root on test for pytest plugin, because of mininet. [David
  Diaz]
- Fixed building for Python. [Carlos Miguel Jenkins Perez]
- Fixed abstract metaclass setup for Python 3.4. [Carlos Miguel Jenkins
  Perez]
- Fixed a bug with the send_data and send_command function when default
  and registry is empty. [Carlos Miguel Jenkins Perez]
- Fixed Python 3.4 compatibility issues. [Carlos Miguel Jenkins Perez]
- Fixed URL of dependency. [Carlos Miguel Jenkins Perez]
- Fix module to support Python3. [David Diaz]

  Mininet only works on Python2, so we remove mininet support on Python3
- Add asserts to check that the topology was build on test. [David Diaz]
- Fixed again the identifier issue, as 'sw1' is also a rfc3986 valid URI
  it can be used. Also removed mockup node to use real PyNML nodes.
  [Carlos Miguel Jenkins Perez]
- Fix test to check that link was made on the expected port. [David
  Diaz]
- Skip mininet tests if not run as root. [David Diaz]
- Fixed a couple of bugs. [Carlos Miguel Jenkins Perez]
- Fixed PEP8 warning on setup.py for long line. [Carlos Miguel Jenkins
  Perez]
- Fixed entry point lookup to match documentation. [Carlos Miguel
  Jenkins Perez]
- Fixed base workflow of platform removal. [Carlos Miguel Jenkins Perez]
- Finished documenting the base classes for topology platform plugins.
  [Carlos Miguel Jenkins Perez]
- Added missing modules to auto reference documentation. [Carlos Miguel
  Jenkins Perez]
- Update pynml url on requirements. [David Diaz]


