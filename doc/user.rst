.. toctree::

.. highlight:: sh

==========
User Guide
==========

Installing
==========

::

   pip install topology

Topology requires at least one **Platform Engine** which is the engine
responsible  to build the topology. By default topology just includes a debug
dummy platform only. We recommend to use the topology_docker_ engine which
can be installed with:

::

   pip install topology_docker

Further setup is required, in particular it is required to install docker and
setup your environment to run some commands as root. See the topology_docker_
documentation for more information.

.. _topology_docker: https://topology_docker.readthedocs.org


Describing topologies
=====================

The Topology framework supports a custom textual format that allows to quickly
specify simple topologies that are only composed of simple nodes, ports and
links between them.

The format for the textual description of a topology is similar to Graphviz
syntax and allows to define nodes and ports with shared attributes and links
between two endpoints with shared attributes too.

::

    # Nodes
    [type=switch attr1=1] sw1 sw2
    hs1

    # Ports
    [speed=1000] sw1:3 sw2:3

    # Links
    [linkattr1=20] sw1: -- sw2:
    [linkattr2=40] sw1:3 -- sw2:3

In the above example two nodes with the attributes ``type`` and ``attr1`` are
specified. Then a third node `hs1` with no particular attributes is defined.
Later, we specify some attributes (speed) for a couple of ports. In the same
way, a link between endpoints MAY have attributes.

An endpoint is a combination of a node and a port name, but the port is
optional. If the endpoint just specifies the node (``sw1:``) then the next
available numeric port is implied.

Is up to the *Platform Engine* to determine what attributes are relevant to it.
By default, the only ones interpreted by the framework is ``identifier`` which
must be an unique UUID (and if missing it will be automatically assigned) and
the ``name`` which is a human readable name used for plotting.

For a more programmatic format consider the ``metadict`` format or using the
:class:`pynml.manager.ExtendedNMLManager` directly.


Using the topology executable
=============================

The ``topology`` executable allows to build topologies on demand and interact
with them. The ``topology`` program allows to launch a topology from a textual
description or from a test (see below). The ``topology`` program is installed
as part of the Topology framework.

::

   $ topology --help
   usage: topology [-h] [-v] [--version] [--platform {debug}] [--non-interactive]
                   [--show-build-commands] [--plot-dir PLOT_DIR]
                   [--plot-format PLOT_FORMAT] [--nml-dir NML_DIR]
                   topology

   Network Topology Framework using NML, with support for pytest.

   positional arguments:
     topology              File with the topology description to build

   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         Increase verbosity level
     --version             show program's version number and exit
     --platform {debug}    Platform engine to build the topology with
     --non-interactive     Just build the topology and exit
     --show-build-commands
                           Show commands executed in nodes during build
     --plot-dir PLOT_DIR   Directory to auto-plot topologies
     --plot-format PLOT_FORMAT
                           Format for plotting topologies
     --nml-dir NML_DIR     Directory to export topologies as NML XML

You can run a topology and interact with their nodes:

::

   $ cat my_topology.net
   # +-------+                                 +-------+
   # |       |     +-------+     +-------+     |       |
   # |  hs1  <----->  sw1  <----->  sw2  <----->  hs2  |
   # |       |     +-------+     +-------+     |       |
   # +-------+                                 +-------+

   # Nodes
   [type=openvswitch name="Switch 1"] sw1
   [type=openvswitch name="Switch 2"] sw2
   [type=host name="Host 1"] hs1
   [type=host name="Host 2"] hs2

   # Links
   hs1:1 -- sw1:3
   sw1:4 -- sw2:3
   sw2:4 -- hs2:1

This topology can be run and interacted with like this:

::

   $ topology --platform=docker my_topology.net
   Starting Network Topology Framework v0.1.0
   Building topology, please wait...
   Engine nodes available for communication:
       sw1, sw2, hs1, hs2
   >>> response = hs1('uname -r', shell='bash')
   [hs1].send_command(uname -r) ::
   3.13.0-23-generic
   >>> response
   '3.13.0-23-generic'


Using with pytest
=================

The topology framework install a pytest plugin that provides, among other
things the ``topology`` fixture. This fixture is a module level fixture that
will try to find a global variable called ``TOPOLOGY`` with the textual
description of the topology. If found, it will parse it and build it with the
platform engine specified with the new pytest ``--topology-platform``
parameter.

Test will be able to interact with the topology nodes by calling
``topology.get('nodeid')`` function. When all test are done, the fixture will
unbuild the topology automatically. In other words, all tests in a module
share the same topology.

.. code:: python

   TOPOLOGY = """
   # +-------+                                 +-------+
   # |       |     +-------+     +-------+     |       |
   # |  hs1  <----->  sw1  <----->  sw2  <----->  hs2  |
   # |       |     +-------+     +-------+     |       |
   # +-------+                                 +-------+

   # Nodes
   [type=openvswitch name="Switch 1"] sw1
   [type=openvswitch name="Switch 2"] sw2
   [type=host name="Host 1"] hs1
   [type=host name="Host 2"] hs2

   # Links
   hs1:1 -- sw1:3
   sw1:4 -- sw2:3
   sw2:4 -- hs2:1
   """

   def test_example(topology):
       """
       Example text for topology.
       """
       sw1 = topology.get('sw1')
       sw2 = topology.get('sw2')
       hs1 = topology.get('hs1')
       hs2 = topology.get('hs2')

       assert sw1 is not None
       assert sw2 is not None
       assert hs1 is not None
       assert hs2 is not None

       # Assert that Linux kernel version >= 3
       version = hs1('uname -r').split('.')
       assert version[0] >= 3


Added pytest arguments
++++++++++++++++++++++

:``--topology-platform``:
   Platform Engine to build the topology with.

:``--topology-plot-dir``:
   Directory to auto-plot topologies.
   All topologies found will be plotted to this directory automatically.

:``--topology-plot-format``:
   Format for ploting topologies (default 'svg')
   This option requires Graphviz installed.

:``--topology-nml-dir``:
   Directory to export topologies as NML XML.
   All topologies found will be exported to NML XML to this directory
   automatically.


Added pytest markers
++++++++++++++++++++

:``test_id(id)``:
   Assign a test identifier to the test.
   The test id will __always__ be added to the jUnit XML report.

   For example:

   .. code:: python

      from pytest import mark
      @mark.test_id(10000)
      def test_example(topology):
         ...

:``platform_incompatible(platforms)``:
   Mark a test as incompatible with a list of platform engines.
   The test will be skipped automatically if it is attempted to be run with an
   incompatible platform.

   For example:

   .. code:: python

      from pytest import marl
      @mark.platform_incompatible(['debug'])
      def test_example(topology):
         ...
