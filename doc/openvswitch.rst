=================
OVS Topology Node
=================

Open vSwitch Kernel Module 
--------------------------
Open vSwitch requires the openvswitch kernel module to be loaded in the host 
machine. The OVS images should work in user space mode without the module 
but this experimental mode was not working in Docker at the time of 
writing. The recommended way to run OVS is to first install the module included 
with the corresponding OVS release. Check the docker image's OVS version by 
looking at its tag or spawning a container. `Download <http://openvswitch.org/download/>`_ 
the corresponding OVS version, build OVS and load the kernel module:

::

   ./configure --with-linux=/lib/modules/`uname -r`/build`
   make
   make modules_install
   /sbin/modprobe openvswitch

Check the `OVS FAQ <https://github.com/openvswitch/ovs/blob/master/FAQ.md#q-what-linux-kernel-versions-does-each-open-vswitch-release-work-with>`_ for information on kernel version support.

Using Open vSwitch Nodes
------------------------

The OpenvSwitch node in Topology looks for the
``socketplane/openvswitch:latest`` docker image by default. The only shell
available to OpenvSwitch is bash, which allows running:

- ``ovs-appclt`` commands, to control the OVS daemon.
- ``ovs-oftcl``, to configure OpenFlow.
- ``ovs-vsctl`` to configure the switch.

For example, you may bring up a bridge with:

::

   # Create a bridge
   sw1('ovs-vsctl add-br br0')

   # Bring up ovs interface
   sw1('ip link set br0 up')

   # Add the front ports
   sw1('ovs-vsctl add-port br0 1')
   sw1('ovs-vsctl add-port br0 2')

Interfaces should be up before the call to add-port. You can create them and
bring them up manually or using the topology definition:

::

   [up=True] sw1:1
   [up=True] sw1:2


Using the Ryu Controller
------------------------

The Ryu controller is made available as a Topology node. The implementation is
based on `osrg's ryu Dockerfiles <https://github.com/osrg/dockerfiles>`_.

Ryu supports applications, which are written in Python as described in the
`Ryu documentation <http://ryu.readthedocs.org/en/latest/>`_.

To start a Ryu node declare it in your topology as:

::

   [type=ryu name="Ctrl 1" app="/path/to/my/app/ryu.py"] ctrl

The app parameter is the path to a python Ryu application. The sample
``simple_switch`` application is run by default. Use an absolute path here,
preferably with a base path set by an environment variable for portability.
Your application will be run as:

::

   PYTHONPATH=. ryu-manager my-app.py --verbose

``ryu-manager`` will listen for connections in every available interface.
The stdout log is accessible in the container at ``/tmp`` or in your host
machine at ``/tmp/topology_<NODE_NAME>_<NODE_ID>``.

You may include any specific ryu-manager options by killing the process with:

::

   switch('supervisorctl stop ryu-manager')

And then manually running it, but be sure to send it to the background:

::

   switch('PYTHONPATH=. ryu-manager my-app.py --verbose &>/tmp/ryu.log &')

You may also pass your own RYU_COMMAND environment variable to supervisor and
re-run the daemon:

::

   switch('RYU_COMMAND="/path/to/ryu-manager /path/to/my-app.py --verbose" supervisord')

You may have to remove the supervisor sock file with:

::

   switch('unlink /var/run/supervisor.sock')

Once the controller instance is running, you should be able to establish a TCP
connection from any reachable switch. Ryu will listen at all interfaces by
default. For OVS:

::

   # Add the front port connecting to the controller
   sw1('ovs-vsctl add-port br0 1')

   # Drop packets if the connection to controller fails
   sw1('ovs-vsctl set-fail-mode br0 secure')

   # Remove the front port's IP address
   sw1('ifconfig 1 0 up')

   # Give the virtual switch an IP address
   sw1('ifconfig br0 10.0.10.2 netmask 255.255.255.0 up')

   # Connect to the OpenFlow controller
   sw1('ovs-vsctl set-controller br0 tcp:10.0.10.1:6633')

   # Wait for OVS to connect to controller
   time.sleep(5)

   # Assert that switch is connected to Ryu
   vsctl_sw1_show = sw1('ovs-vsctl show')
   assert 'is_connected: true' in vsctl_sw1_show


Debugging OpenvSwitch and Ryu
-----------------------------

Ryu and Openvswitch are both started by supervisor.

- If you have access to the running container, supervisorctl allows you to
  check the status and logs of the ryu, ovs-switchd and ovsdb-server processes.
- If the Topology startup fails, stdout and stderr logs for every supervisor
  process are kept in the container at the /tmp folder, which is shared with
  your host machine at ``/tmp/topology_<NODE_NAME>_<NODE_ID>``, so that you are
  able to check those logs afterwards.
- Check the ``supervisord.conf`` file for details on how the services are being
  started.


The OVS docker switch
---------------------

The following section explains the process used to build the docker OVS image.
It may be useful for advanced users when creating or customizing the docker
image but not when writing tests using the default features.

The OVS docker switch was built making use of
`socketplane's docker-ovs images <https://github.com/socketplane/docker-ovs>`_.

Each folder corresponds to an OpenVswitch version and includes the Dockerfile
and two required files.

- OVS is brought up by supervisor. The ``supervisord.conf`` file is copied to
  the container to be run by supervisor.
- ``configure-ovs.sh`` executes some OVS startup commands.

Depending on you environment, you may need to set a proxy in the building
container, by setting the http_proxy and https_proxy variables in the
Dockerfile:

::

   ENV http_proxy http://proxy.houston.hp.com:8080/
   ENV https_proxy http://proxy.houston.hp.com:8080/

Then simply build the Docker image with:

::

   cd version_folder
   docker build -t openvswitch:latest .

This creates an OVS docker image with the required capabilities. The image auto
starts supervisord with ``nodaemon=true``. This is undesirable in topology since
it blocks sdtin, and should be disabled in the ``supervisord.conf`` file.
