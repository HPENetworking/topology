# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Test suite for module topology.injection.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from os.path import join
from shutil import rmtree
from collections import OrderedDict

# Reload module to properly measure coverage
from six.moves import reload_module
import topology.pytest.plugin

from topology.manager import TopologyManager
from pyszn.injection import parse_attribute_injection

reload_module(topology.pytest.plugin)

TOPOLOGY_TO_BUILD = """
# Nodes
[shell=vtysh name="Switch 9"] sw9
[shell=vtysh name="Switch 2"] sw2
[type=switch name="Switch 8"] sw8
[type=host name="Host 3"] hs3
[type=host name="Host 2"] hs2
# Links
hs3:1 -- sw9:1
hs2:1 -- sw2:1
[attr1=value1] sw9:2 -- sw2:2
"""

TOPOLOGY_MATCH_0 = """
# Nodes
[shell=vtysh name="Switch 1"] sw1
[shell=vtysh name="Switch 2"] sw2
[type=switch name="Switch 8"] sw8
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2
# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
[attr1=1] sw1:2 -- sw2:2
"""

TOPOLOGY_MATCH_1 = """
# Nodes
[shell=vtysh name="Switch 1"] sw1
[shell=vtysh name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2
# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
[attr1=1] sw1:2 -- sw2:2
"""

TOPOLOGY_MATCH_2 = """
# Nodes
[shell=vtysh name="Switch 1"] sw4
[shell=vtysh name="Switch 2"] sw5
"""

TOPOLOGY_MATCH_3 = """
# Nodes
[shell=vtysh name="Switch 1"] sw6
[shell=vtysh name="Switch 2"] sw7
[type=host name="Host 1"] hs3
[type=host name="Host 2"] hs4
# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
[attr1=1] sw1:2 -- sw2:2
"""

TOPOLOGY_MATCHES = {
    '0': TOPOLOGY_MATCH_0,
    '2': TOPOLOGY_MATCH_2
}

TOPOLOGY_MATCHES_FOLDER = {
    '1': TOPOLOGY_MATCH_1,
    '3': TOPOLOGY_MATCH_3
}

INJECTION_FILE = """
[
    {{
        "files": ["test_topology_match_0.py"],
        "modifiers": [
            {{
                "nodes": ["sw1"],
                "attributes": {{
                    "image": "image_for_sw1",
                    "hardware": "hardware_for_sw1"
                }}
            }},
            {{
                "nodes": ["sw2"],
                "attributes": {{
                    "image": "image_for_sw2",
                    "shell": "vtysh",
                    "name":  "new_name"
                }}
            }},
            {{
                "nodes": ["type=switch"],
                "attributes": {{
                    "chassis": "chassis_for_sw8"
                }}
            }}
        ]
    }},
    {{
        "files": [
            "test_topology_match_0.py",
            "test_topology_match_1.py"
        ],
        "modifiers": [
            {{
                "nodes": ["sw1", "type=host", "sw3"],
                "attributes": {{
                    "image": "image_for_sw1_sw3_hs1_hs2",
                    "hardware": "hardware_for_sw1_sw3_hs1_hs2"
                }}
            }},
            {{
                "nodes": ["sw4"],
                "attributes": {{
                    "image": "image_for_sw4"
                }}
            }}
        ]
    }},
    {{
        "files": ["test_topology_match_2.py"],
        "modifiers": [
            {{
                "nodes": ["*"],
                "attributes": {{
                    "image": "image_for_sw4_sw5"
                }}
            }}
        ]
    }},
    {{
        "files": ["*"],
        "modifiers": [
             {{
                "links": ["hs2:1 -- sw2:1"],
                "attributes": {{
                    "link_attr": "link_value"
                }}
           }},
           {{
                "ports": ["sw2:1"],
                "attributes": {{
                    "port_attr": "port_value"
                }}
            }},
            {{
                "nodes": ["hs*"],
                "attributes": {{
                    "image": "image_for_all_hosts"
                }}
            }},
            {{
                "nodes": ["sw6", "sw7"],
                "attributes": {{
                    "image": "image_for_sw6_sw7"
                }}
            }}
        ]
    }}
]
"""

EXPECTED_PARSED_INJECTION_FILE = OrderedDict([
    (
        '{search_path}/test_topology_match_0.py',
        OrderedDict([
            (
                'sw1', {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ), (
                'sw2', {
                    'image': 'image_for_sw2',
                    'shell': 'vtysh',
                    'name': 'new_name',
                }
            ), (
                'sw8', {
                    'chassis': 'chassis_for_sw8'
                }
            ), (
                'hs1', {
                    'image': 'image_for_all_hosts',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ), (
                'hs2', {
                    'image': 'image_for_all_hosts',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ),
        ])
    ), (
        '{search_path}/subfolder/test_topology_match_1.py',
        OrderedDict([
            (
                'sw1', {
                    'image': 'image_for_sw1_sw3_hs1_hs2',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ), (
                'hs1', {
                    'image': 'image_for_all_hosts',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ), (
                'hs2', {
                    'image': 'image_for_all_hosts',
                    'hardware': 'hardware_for_sw1_sw3_hs1_hs2',
                }
            ),
        ])
    ), (
        '{search_path}/test_topology_match_2.py',
        OrderedDict([
            (
                'sw4', {
                    'image': 'image_for_sw4_sw5',
                }
            ), (
                'sw5', {
                    'image': 'image_for_sw4_sw5',
                }
            ),
        ])
    ), (
        '{search_path}/subfolder/test_topology_match_3.py',
        OrderedDict([
            (
                'hs3', {
                    'image': 'image_for_all_hosts',
                }
            ), (
                'hs4', {
                    'image': 'image_for_all_hosts',
                }
            ), (
                'sw6', {
                    'image': 'image_for_sw6_sw7',
                }
            ), (
                'sw7', {
                    'image': 'image_for_sw6_sw7',
                }
            ),
        ])
    )]
)


def test_attribute_injection(tmpdir):
    """
    Test the configuration file is parsed correctly.
    """
    workdir = str(tmpdir)
    search_path = str(tmpdir.mkdir('test'))
    subfolder = str(tmpdir.mkdir('test/subfolder'))

    try:
        # Write matching topologies
        for basepath, matches in (
                (search_path, TOPOLOGY_MATCHES),
                (subfolder, TOPOLOGY_MATCHES_FOLDER)):
            for count, content in matches.items():
                output_filename = join(
                    basepath, 'test_topology_match_{}.py'.format(count)
                )
                with open(output_filename, 'w') as fd:
                    fd.write('TOPOLOGY = """\n')
                    fd.write(content)
                    fd.write('"""')

        # Write the attributes injection file
        injection_path = join(workdir, 'attributes_injection.json')
        with open(injection_path, 'w') as fd:
            fd.write(INJECTION_FILE.format(search_path=search_path))

        # Change keys of the expected parsed injection file
        expected = OrderedDict()
        for key, value in EXPECTED_PARSED_INJECTION_FILE.items():
            expected[key.format(search_path=search_path)] = value

        # Actually parse the injection file
        actual = parse_attribute_injection(
            injection_path, search_paths=[search_path]
        )

        # Test building with injected attributes
        injected_attributes = actual[
            '{search_path}/test_topology_match_0.py'.format(
                search_path=search_path
            )
        ]

        topology = TopologyManager()
        topology.parse(
            TOPOLOGY_TO_BUILD,
            inject=injected_attributes
        )
        topology.build()

        sw9 = topology.get('sw9')
        sw2 = topology.get('sw2')
        sw8 = topology.get('sw8')
        hs3 = topology.get('hs3')
        hs2 = topology.get('hs2')

        assert sw9.metadata == {
            'shell': 'vtysh',
            'name': 'Switch 9'
        }
        assert sw2.metadata == {
            'image': 'image_for_sw2',
            'shell': 'vtysh',
            'name': 'new_name'
        }
        assert sw8.metadata == {
            'type': 'switch',
            'name': 'Switch 8',
            'chassis': 'chassis_for_sw8'
        }
        assert hs3.metadata == {
            'type': 'host',
            'name': 'Host 3'
        }
        assert hs2.metadata == {
            'type': 'host',
            'name': 'Host 2',
            'image': 'image_for_all_hosts',
            'hardware': 'hardware_for_sw1_sw3_hs1_hs2'
        }

    finally:
        try:
            rmtree(workdir)
        except:
            pass
