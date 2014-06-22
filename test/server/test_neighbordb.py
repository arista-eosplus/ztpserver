#
# Copyright (c) 2014, Arista Networks, Inc.
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

from mock import patch

import ztpserver.neighbordb

from server_test_lib import random_string
from server_test_lib import create_neighbordb

class NeighbordbUnitTests(unittest.TestCase):

    def test_default_filename(self):
        result = ztpserver.neighbordb.default_filename()
        self.assertEqual(result, '/usr/share/ztpserver/neighbordb')

    @patch('ztpserver.neighbordb.load')
    def test_load_file(self, m_load):
        result = ztpserver.neighbordb.load_file(random_string(),
                                                random_string())
        self.assertEqual(result, m_load.return_value)

    @patch('ztpserver.neighbordb.validate_topology')
    @patch('ztpserver.neighbordb.load')
    def test_load_file_failure(self, m_load):
        m_load.side_effect = ztpserver.serializers.SerializerError
        self.assertIsNone(ztpserver.neighbordb.load_file(random_string(),
                                                         random_string()))

    @patch('ztpserver.neighbordb.validate_topology')
    @patch('ztpserver.neighbordb.load')
    def test_load_topology(self, m_validate_topology, m_load):
        contents = '''
            variables:
                foo: bar
            patterns:
                - any: any
        '''
        m_load.return_value = yaml.load(contents)
        result = ztpserver.neighbordb.load_topology()
        self.assertIsNotNone(result)




    def test_replace_config_action(self):
        resource = random_string()
        result = ztpserver.neighbordb.replace_config_action(resource)
        self.assertEqual('install static startup-config file', result['name'])
        self.assertEqual('replace_config', result['action'])
        self.assertTrue(result['always_execute'])


if __name__ == '__main__':
    unittest.main()
