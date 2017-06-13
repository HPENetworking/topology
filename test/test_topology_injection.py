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
from deepdiff import DeepDiff

from pytest import fixture

from topology.manager import TopologyManager
from topology.injection import parse_attribute_injection

reload_module(topology.pytest.plugin)

# This SZN string will be used to actually build a topology while using
# injected attributes. This means that the injected attributes will either
# override or add to the attributes defined for the elements in this constant.
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

# This and the following TOPOLOGY_MATCH_X are constants that will be written
# into files with matching topology_match_X.py names.
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

# This gathering of the constants into dictionaries is done only to make the
# handling of them more convenient.
TOPOLOGY_MATCHES = {
    '0': TOPOLOGY_MATCH_0,
    '2': TOPOLOGY_MATCH_2
}

TOPOLOGY_MATCHES_FOLDER = {
    '1': TOPOLOGY_MATCH_1,
    '3': TOPOLOGY_MATCH_3
}

# This is the content of a .json injection file. Read the following comments
# for more information.
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
                "links": ["hs1:1 -- sw1:1"],
                "attributes": {{
                    "rate": "slow"
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

# This is the expected ordered dictionary that should result after parsing the
# injection file.
# Because of the fact that the final path where the test_topology_match_X.py
# files will be created is still unknown, there is a placeholder for the paths
# that will be filled with the actual file path later.
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
                'hs1:1 -- sw1:1', {
                    'rate': 'slow',
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


@fixture
def arranger(tmpdir):
    # This temporary directory is created to serve as a root directory to other
    # temporary directories.
    workdir = str(tmpdir)

    # These subdirectories will be used to host .py files that contain a SZN
    # string. These SZN strings are the ones in the TOPOLOGY_MATCH_X constants.
    # FIXME: Verify the next statement:
    # The purpose of these subdirectories is to serve as different paths that
    # can be used to test the file expansion feature of attribute injection.
    search_path = str(tmpdir.mkdir('test'))
    subfolder = str(tmpdir.mkdir('test/subfolder'))

    # Filling the path placeholders in EXPECTED_PARSED_INJECTION_FILE, see the
    # comment above that constant for more information.
    expected = OrderedDict()
    for key, value in EXPECTED_PARSED_INJECTION_FILE.items():
        expected[key.format(search_path=search_path)] = value

    return {
        'workdir': workdir,
        'search_path': search_path,
        'subfolder': subfolder,
        'expected': expected
    }


def test_attribute_parsing(arranger):
    """
    Test the parsing for attribute injection.

    In this test case, several files will be created:
    1. Several test_topology_match_X.py files: they will contain each a SZN
       string only.
    2. One attributes_injection.json file: this will contain a JSON
       specification of attributes that will be injected to the topologies
       defined in the previous files.

    Once that is done, the parse_attribute_injection function will be called
    with the path to a root folder that holds all the
    test_topology_match_X.py files and with the path to the recently created
    attributes_injection.json file. This function will return a dictionary that
    defines which attributes will be injected to which elements in which SZN
    strings.

    This test will verify that parse_attribute_injection returns the correct
    dictionary by comparing it to the SZN strings and to the JSON file.
    """

    workdir = arranger['workdir']
    search_path = arranger['search_path']
    subfolder = arranger['subfolder']
    expected = arranger['expected']

    try:
        # The contents of the TOPOLOGY_MATCH_X constants will be written into
        # matching test_topology_match_X.py files.
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

        # Write the attributes injection file attributes_injection.json with
        # the contents of INJECTION_FILE.
        injection_path = join(workdir, 'attributes_injection.json')
        with open(injection_path, 'w') as fd:
            fd.write(INJECTION_FILE.format(search_path=search_path))

        # At these moment, the following file structure exists:
        #   /path/to/workdir/
        #       attributes_injection.json
        #       test/
        #           test_topology_match_0.py
        #           test_topology_match_2.py
        #           subfolder/
        #               test_topology_match_1.py
        #               test_topology_match_3.py

        # Parse the injection file. The /path/to/workdir/test is used here in
        # search_path to test the searching of SZN strings in several files
        # located in nested folders.
        actual = parse_attribute_injection(
            injection_path, search_paths=[search_path]
        )

        # Compare the actual and the expected ordered dictionaries, there
        # should be no differences.
        differences = DeepDiff(actual, expected)
        assert not differences

    finally:
        try:
            rmtree(workdir)
        except:
            pass


def test_attribute_injection_build(arranger):
    """
    Test the building of a topology with injected attributes.

    In this test case, a known topology will be built with injected attributes.
    This will test the correct overriding or adding of the injected attributes
    to the ones that were already present in the known topology
    """

    workdir = arranger['workdir']
    search_path = arranger['search_path']
    expected = arranger['expected']

    try:
        # An actual topology will be built using injected attributes from an
        # injection dictionary. The attributes present in this dictionary will
        # be injected to the SZN string defined in test_topology_match_0.py.
        injected_attributes = expected[
            '{search_path}/test_topology_match_0.py'.format(
                search_path=search_path
            )
        ]

        topology = TopologyManager()

        # The topology is built here with the attributes from the injection
        # dictionary. Read the comment above the definition of
        # TOPOLOGY_TO_BUILD for more information.
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

        # The SZN string in test_topology_match_0.py includes this node:
        # [type=switch name="Switch 8"] sw8

        # The injection file includes this specification:
        # 'sw8', {
        #     'chassis': 'chassis_for_sw8'
        # }

        # So, after building, sw8 should have 'chassis' in its metadata.

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
