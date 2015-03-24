#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import unittest
import yaml

from mock import patch, Mock

import ztpserver.serializers
import ztpserver.topology

from ztpserver.topology import Neighbordb, Pattern
from ztpserver.topology import create_node, load_file, load_neighbordb
from ztpserver.topology import neighbordb_path, replace_config_action
from ztpserver.topology import load_pattern
from server_test_lib import enable_logging, random_string

class NeighbordbUnitTests(unittest.TestCase):

    def test_neighbordb_path(self):
        result = neighbordb_path()
        self.assertEqual(result, '/usr/share/ztpserver/neighbordb')

    @patch('ztpserver.topology.load')
    def test_load_file(self, m_load):
        result = load_file(random_string(),
                           random_string(),
                           random_string())
        self.assertEqual(result, m_load.return_value)

    @patch('ztpserver.topology.validate_neighbordb')
    @patch('ztpserver.topology.load')
    def test_load_file_failure(self, m_load, _):
        m_load.side_effect = ztpserver.serializers.SerializerError
        self.assertRaises(ztpserver.serializers.SerializerError,
                          load_file,
                          random_string(),
                          random_string(),
                          random_string())

    @patch('ztpserver.topology.validate_neighbordb')
    @patch('ztpserver.topology.load')
    def test_load_neighbordb(self, _, m_load):
        contents = '''
            variables:
                foo: bar
            patterns:
                - name: dummy pattern
                  definition: dummy_definition
                  interfaces:
                    - any: any
        '''
        m_load.return_value = yaml.load(contents)
        result = load_neighbordb(random_string())
        self.assertIsNotNone(result)

    @patch('ztpserver.topology.load')
    def test_load_neighbordb_no_variables(self, m_load):
        # github issue #114
        contents = """
            patterns:
                - name: dummy pattern
                  definition: dummy_definition
                  interfaces:
                    - any: any
        """
        m_load.return_value = yaml.load(contents)
        result = load_neighbordb(random_string())
        self.assertIsInstance(result, Neighbordb)

    def test_load_pattern_minimal(self):
        pattern = load_pattern({'name': random_string(),
                                'definition': random_string(),
                                'interfaces': []})
        self.assertIsInstance(pattern, Pattern)

    def test_load_pattern_with_interfaces(self):
        # github issue #128
        contents = """
            name: test
            # Default pattern - always succeeds
            definition: dummy_definition
            interfaces:
                - any: any:any
        """
        kwargs = yaml.load(contents)
        pattern = load_pattern(kwargs)
        self.assertIsInstance(pattern, Pattern)

    def test_replace_config_action(self):
        resource = random_string()
        result = replace_config_action(resource)
        self.assertEqual('install static startup-config file', result['name'])
        self.assertEqual('replace_config', result['action'])
        self.assertTrue(result['always_execute'])

    def test_create_node_fixup_systemmac_colon(self):
        attrs = Mock(systemmac='99:99:99:99:99:99')
        result = create_node({'systemmac': 
                              attrs.systemmac})
        self.assertTrue(':' not in result.systemmac)

    def test_create_node_fixup_systemmac_period(self):
        attrs = Mock(systemmac='99.99.99.99.99.99')
        result = create_node({'systemmac': 
                              attrs.systemmac})
        self.assertTrue('.' not in result.systemmac)

if __name__ == '__main__':
    enable_logging()
    unittest.main()
