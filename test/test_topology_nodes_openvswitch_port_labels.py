

"""
OpenSwitch Test for vlan related configurations.
"""

from time import sleep

TOPOLOGY = """
# +-------+                    +-------+
# |       |     +--------+     |       |
# |  hs1  <----->  ops1  <----->  hs2  |
# |       |     +--------+     |       |
# +-------+                    +-------+

# Nodes
[type=openswitch name="OpenSwitch 1"] ops1
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:IF01 -- ops1:IF01
ops1:IF02 -- hs2:IF01
"""


def test_topology_nodes_openvswitch_port_labels(topology):
    ops1 = topology.get('ops1')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    assert ops1 is not None
    assert hs1 is not None
    assert hs2 is not None

    ops1("configure terminal")
    ops1("interface " + str(ops1.ports['IF01']))
    ops1("no shutdown")
    ops1("end")
    sleep(5)
    result = ops1("show interface " + str(ops1.ports['IF01']))
    assert result != "% Unknown command."
