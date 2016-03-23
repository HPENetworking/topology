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

Platform Engines are plugins that define how a topology is built.

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

Vtysh
+++++

The Vtysh communication library allows to abstract contexts and commands for
OpenSwitch_'s vtysh interactive shell.

.. toctree::
   :includehidden:

   reference/topology_lib_vtysh

.. _OpenSwitch: http://openswitch.net/
