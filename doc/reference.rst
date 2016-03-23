===========================
API Reference Documentation
===========================

This page was generated thanks to the Sphinx AutoAPI_ extension.

.. _AutoAPI: http://autoapi.readthedocs.org/

.. contents::
   :local:


Framework Core
==============

.. toctree::
   :includehidden:

   reference/topology


Platform Engines
================

*Platform Engines* are plugins that define how a topology is built.

.. contents::
   :local:


Docker
++++++

The ``topology_docker`` Platform Engine builds a topology using Docker_
containers for each node and interconnects them using virtual interfaces.

.. _Docker: https://www.docker.com/

.. toctree::
   :includehidden:

   reference/topology_docker


Connect
+++++++

The ``topology_connect`` Platform Engine assumes the topology is a
representation of an already built physical topology and connects to the nodes
using SSH and Telnet connections.

.. toctree::
   :includehidden:

   reference/topology_connect


Communication Libraries
=======================

*Communication Libraries* are glue Software components that allow to talk the
dialect a node speaks. Be it a REST API, SNMP, specialized interactive terminal,
commands, etc.

Ping
++++

Communication library for the Linux ``ping`` command.

.. toctree::
   :includehidden:

   reference/topology_lib_ping


IP
++

Communication library for the Linux ``ip`` command that allows to setup ip
addresses, routes, etc.

.. toctree::
   :includehidden:

   reference/topology_lib_ip


Vtysh
+++++

The Vtysh communication library allows to abstract contexts and commands for
OpenSwitch_'s vtysh interactive shell.

.. _OpenSwitch: http://openswitch.net/

.. toctree::
   :includehidden:

   reference/topology_lib_vtysh
