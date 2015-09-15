.. toctree::

.. highlight:: python

=========================
Plugins Development Guide
=========================

Entry Point
===========

Our entry point is ``topology_platform_<api_version>``, currently
``topology_platform_10``.

To extend `topology` to support your platform first implement in your module a
subclass of :class:`topology.platforms.base.BasePlatform`.

It is recommended, but not required, that your module is called
``topology_<platform_name>`` and your sublcass is called
``<PlatformName>Platform``.

For example, in your module ``topology_my.plugin``:

::

   from topology.platforms.base import BasePlatform
   class MyPlatform(BasePlatform):
       pass

Then specify in your `setup.py`:

::

   # Entry points
   entry_points={
       'topology_platform_10': ['my = topology_my.plugin:MyPlatform']
   }


Engine Platform Worflow
=======================

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
        M <<-- P: <<return>>
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
