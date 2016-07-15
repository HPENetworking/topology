.. toctree::

=========================
Plugins Development Guide
=========================

The Topology framework is easily extendable. In particular, you can extend the
platform where the topology is built and run (virtual, physical, etc) and
extend the mechanisms available to communicate with the nodes (shells like
vtysh or bash, RESTful API, OpenFlow, OVSDB management protocol, protobuffers,
etc).

.. contents::
   :local:


Provide a new Platform Engine
=============================

An Platform Engine is a system that allows to build and run a topology
description. The Topology framework only provides a built-in Platform Engine
for debugging. You can provide your own or install any of the known Engine
Platforms available as plugins like:

- `Docker <http://topology-docker.readthedocs.org/>`_.


Entry Point
-----------

The entry point to provide a new Platform Engine is
``topology_platform_<api_version>``, currently ``topology_platform_10``.

To extend `topology` to support your platform first implement in your package a
subclass of :class:`topology.platforms.platform.BasePlatform`.

It is recommended, but not required, that your package is called
``topology_<platform_name>`` and your sublcass is called
``<PlatformName>Platform``.

For example, in your module ``topology_my.platform``:

.. code-block:: python

    from topology.platforms.platform import BasePlatform
    class MyPlatform(BasePlatform):
        pass

Then specify in your `setup.py`:

.. code-block:: python

    # Entry points
    entry_points={
        'topology_platform_10': ['my = topology_my.platform:MyPlatform']
    }


.. _engine-platform-worflow:

Platform Engine Worflow
-----------------------

The new platform needs to implement a set of hooks that will be called during
the build and unbuild phases of a topology setup. For a textual description of
each hook please consult the :class:`topology.platforms.platform.BasePlatform`
class.

The following sequence diagram shows the interaction between the
:class:`topology.manager.TopologyManager`, which drives the lifecycle of a
topology, and the *Platform Engine* which is responsible of building and
running the topology itself.

The interaction is straightforward, the main detail is that the ``add_node``
hook receives a *Specification Node* in standard NML format and must return a
*Engine Node*, which is a different type of node that possess a communication
interface. Users of the topology interact with *Engine Nodes*, not with
*Specification Nodes*. Is up to the *Platform Engine* to implement the one
(or many) *Engine Nodes*. Each *Engine Node* inherits from the
:class:`topology.platforms.node.BaseNode` class and must implement its
interface.

Another detail is that the *Platform Engine* must return the real or final port
name of a given *Specification port* in the ``add_biport`` hook. This allows
to the engine to change names to map to a specific platform or to change layout
or perform autoport connections. With this mapping the user will be able to
reference a port using the specification name and it could be mapped to the
real port name.

.. uml::
    :width: 100%

    actor User as U
    participant TopologyManager as M
    participant "platform: BasePlatform" as P
    participant "enode : BaseNode" as N

    U -->> M: <<create>>(engine)
    activate M
    U -> M: load(dict), parse(str), register_node(node)
    U <<-- M: <<return>>
    U -> M: build()
    M -->> P: <<create>>(timestamp, nml)
    activate P
    M -> P: pre_build()
    M <<-- P: <<return>>

    loop each node
        M -> P: add_node(node)
        P -->> N: <<create>>()
        activate N
        M <<-- P: enode
        M -> M: register(enode)
    end

    loop each biport
        M -> P: add_biport(node, biport)
        M <<-- P: eport
        M -> M: register(eport)
    end

    loop each bilink
        M -> P: add_bilink(node_port_a, node_port_b, bilink)
        M <<-- P: <<return>>
    end

    M -> P: post_build()
    M <<-- P: <<return>>

    U <<-- M: <<return>>

    loop as needed
        U -> M: get(enode_name)
        M -->> U: enode
        U -> N: send_command(cmd)
        U <<-- N: response
    end

    U -> M: unbuild()
    M -> P: destroy()
    M <-- P: <<return>>
    destroy P
    destroy N
    U <-- M: <<return>>


.. _provide-a-new-communication-library:

Provide a new Communication Library
===================================

A communication library is a component that a allows an *Engine Node* to speak
in a particular language or medium. Because the *Platform Engine* is the one
responsible to provide a functional *Engine Node* is up to the
*Platform Engine* to support the use of the communication libraries provided
by this extension mechanism (but it is highly recommended to do so).


Entry Point
-----------

The entry point to provide a new *Communication Library* is
``topology_library_<api_version>``, currently
``topology_library_10``.

To extend `topology` to support your communication library you must implement
in your package a module with all your public functions and classes and create
a registry entry (see below).

It is recommended, but not required, that your package is called
``topology_lib_<library_name>``.

For example, in your module ``topology_lib_my.library``:

.. code-block:: python

    def foo_function(enode, myarg1=None, myarg2=100):
       return {'ham': myarg1}

    def bar_function(enode, myarg1=None, myarg2=100):
       return {'ham': 200}

    class FooClass(object):
        def __init__(self, enode, myarg):
            print(123)

    __all__ = ['foo_function', 'bar_function', 'FooClass']

Then specify in your `setup.py`:

.. code-block:: python

    # Entry points
    entry_points={
        'topology_library_10': ['my = topology_lib_my.library']
    }

With this, and if your *Platform Engine* builds your *Engine Nodes* to support
communication libraries (see below), your functions will be available
to the ``enode`` like this:

.. code-block:: python

    >>> sw1.libs.my.foo_function(myarg1=275)
    {'ham': 275}
    >>> sw1.libs.my.FooClass("hi")
    123

Please note, all your functions and classes are registered inside a namespace
with the name of the communication library as you specified in the ``setup.py``


Saving state
------------

All communication functions and classes receive the *Engine Node* as first
parameter, all other parameters are up to the function. The ``enode`` argument
can be used to store state or data for the library or to trigger calls to other
libraries or commands as part of the communication flow.

A common pattern is to use a class to store the state of the communication
library and store an instances of that class inside the enode. The decorator
:func:`topology.libraries.utils.stateprovider` allows to easily implement this
pattern:

.. code-block:: python

    from topology.libraries.utils import stateprovider

    class MyState(object):
        def __init__(self):
            self.my_variable_one = 100

    @stateprovider(MyState)
    def my_library_function(enode, state, arg1, arg2, keyword_arg1=None):
        print(state.my_variable_one)
        state.my_variable_one += 100

     __all__ = ['my_library_function']


Shell command wrapping libraries
--------------------------------

A common pattern is to use communication libraries to wrap and parse shell
commands.

It is recommended to check first the availability of any dependency shell
using the method :meth:`topology.platforms.node.BaseNode.available_shells`.
See :class:`topology.platforms.node.BaseNode` for more information about the
*Engine Node* interface.

For an example of a communication library that wrap shells commands please
review the topology_lib_ping_ library documentation for more information..

.. _topology_lib_ping: https://github.com/HPENetworking/topology_lib_ping/blob/master/lib/topology_lib_ping/library.py


Supporting communication libraries
----------------------------------

Most of the nodes you use will derive from the common
:class:`topology.platforms.node.CommonNode`. If for some reason you require to
use a different base node, say :class:`topology.platforms.node.BaseNode` and you
still want to support communication libraries make sure to create and attribute
``libs`` with an instance of :class:`topology.libraries.manager.LibsProxy`:

.. code-block:: python

   class MyEngineNode(BaseNode):
       def __init__(self, identifier, **kwargs):
           super(MyEngineNode, self).__init__(identifier, **kwargs)

           # Add support for communication libraries
           self.libs = LibsProxy(self)
