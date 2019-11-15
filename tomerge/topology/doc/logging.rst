.. toctree::

.. highlight:: sh

=====================
Logging with Topology
=====================

Logging Architecture
====================

Topology provides logging capabilities for its own and third party components.
This functionality is implemented in :py:mod:`topology.logging`.

Logging Categories
------------------

The topology components are classified in the following categories:

#. ``core``:
   This category is reserved for the Topology Core components.

   :Audience:
    Core developers.

#. ``library``:
   This category is reserved for any Communication Library plugin logging.

   :Audience:
    Communication Libraries developers.

#. ``platform``:
   This category is reserved for any Platform Engine plugin logging.

   :Audience:
    Platform Engines developers.

#. ``user``:
   This category is reserved for user logging (e.g. test cases).

   :Audience:
    Test cases and end user developers.

#. ``node``:
   This category is reserved for any Node plugin logging (e.g. initialization).

   :Audience:
    Nodes developers.

#. ``shell``:
   This category is reserved for logging any ``node.send_command()`` call.

   :Audience:
    Core developers.

#. ``connection``:
   This category is reserved for logging any ``shell.send_command()`` and
   ``shell.get_response()`` calls.

   :Audience:
    Core developers.

#. ``pexpect``:
   This category is reserved for logging a complete PExpect session.

   :Audience:
    Core developers.

#. ``service``:
   This category is reserved general of services clients.

   :Audience:
    Nodes developers and third party developers using the ServicesAPI for
    service clients.


Logging directory
-----------------

All loggers are provided with a logging directory, taken from the value passed
with the options:

- ``--topology-log-dir``, if using the pytest plugin.
- ``--log-dir``, if using the ``topology`` executable in interactive mode.
- ``topology.logging.manager.logging_directory`` property if using
  programatically.


Logging Levels
--------------

The default level for these loggers is ``INFO``, but this level can be set
using:

- ``topology.logging.manager.set_category_level(category, level)`` method, to
  change the level of all loggers in a category.


Logging Context
---------------

Loggers may also have a defined context, this is useful to provide a unique
identifier for objects associated to a particular escenario. The context
can or will be set to:

- It will be set to ``None`` if using the ``topology`` executable in
  interactive mode.
- It will be set to the name of the **Test Suite** (the ``test_xxx.py`` file
  that holds one or more test cases) if using the pytest plugin.
- ``topology.logging.manager.logging_context`` property if using
  programatically.
