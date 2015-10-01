.. toctree::

.. highlight:: sh

==========
User Guide
==========


Using the topology executable
=============================

The ``topology`` executable allows to build topologies on demand and interact
with them.

::

   $ topology --help
   usage: topology [-h] [-v] [--version] [--platform {debug,docker}]
                   [--non-interactive] [--show-build-commands]
                   topology

   Network Topology Framework using NML, with support for pytest.

   positional arguments:
     topology              File with the topology description to build

   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         Increase verbosity level
     --version             show program's version number and exit
     --platform {debug,docker}
                           Select the platform to build the topology
     --non-interactive     Just build the topology and exit
     --show-build-commands
                           Show commands executed in nodes during build
