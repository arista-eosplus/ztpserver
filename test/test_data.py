#
# Copyright (c) 2013, Arista Networks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import unittest
import os

import ztpserver.config
import ztpserver.data

class TestData(unittest.TestCase):

    def test_create_data(self):
        data = ztpserver.data.Data()
        self.assertIsNotNone(data)

    def test_get_data(self):
        data = ztpserver.data.Data()
        data._data['test'] = 'value'
        self.assertEqual(data['test'], 'value')

    def test_data_length(self):
        data = ztpserver.data.Data()
        self.assertEqual(len(data), 0)
        data._data['test'] = 'value'
        self.assertEqual(len(data), 1)

class TestDataFile(unittest.TestCase):

    def test_load_yaml_valid_filename(self):
        data = "test: value"
        open('/tmp/data.yaml', 'w').write(data)
        datafile = ztpserver.data.DataFile()
        datafile.load('/tmp/data.yaml', content_type='application/yaml')

    def test_load_invalid_filename(self):
        datafile = ztpserver.data.DataFile()
        self.assertRaises(IOError, datafile.load, '/invalid/path/to/file')

    def test_dump_text_valid_filename(self):
        datafile = ztpserver.data.DataFile()
        datafile._data['test'] = 'value'
        datafile.dump('/tmp/data.text')

    def test_dump_json_valid_filename(self):
        datafile = ztpserver.data.DataFile()
        datafile._data['test'] = 'value'
        datafile.dump('/tmp/data.json', content_type='application/json')

    def test_dump_yaml_valid_filename(self):
        datafile = ztpserver.data.DataFile()
        datafile._data['test'] = 'value'
        datafile.dump('/tmp/data.yaml', content_type='application/yaml')

    def test_dump_invalid_filename(self):
        datafile = ztpserver.data.DataFile()
        datafile._data['test'] = 'value'
        self.assertRaises(IOError, datafile.dump, '/invalid/path/to/file')

class TestNodeDb(unittest.TestCase):

    def setUp(self):
        self.nodedb = ztpserver.data.NodeDb()

    def tearDown(self):
        del self.nodedb

    def test_load_nodedb(self):
        data = "---\n'123456789': 'test'\n"
        open('/tmp/nodedb', 'w').write(data)
        ztpserver.config.runtime.set_value('nodedb', '/tmp/nodedb', 'db')
        self.nodedb.load()
        self.assertTrue('123456789' in self.nodedb._data)

    def test_dump_nodedb(self):
        if os.path.exists('/tmp/nodedb'):
            os.remove('/tmp/nodedb')
        ztpserver.config.runtime.set_value('nodedb', '/tmp/nodedb', 'db')
        self.nodedb._data['123456789'] = 'value'
        self.nodedb.dump()
        self.assertTrue(os.path.exists('/tmp/nodedb'))

    def test_insert_new_item(self):
        self.nodedb.insert('123456789', 'test')
        self.assertEqual(self.nodedb['123456789'], 'test')

    def test_insert_existing_item(self):
        self.nodedb.insert('123456789', 'test')
        self.nodedb.insert('123456789', 'test')
        self.assertEqual(len(self.nodedb), 1)

    def test_delete_item_valid(self):
        self.nodedb._data['123456789'] = 'test'
        self.nodedb.delete('123456789')
        self.assertFalse('123456789' in self.nodedb._data)

    def test_delete_item_invalid(self):
        # this test only fails if the delete function isn't silent
        self.nodedb.delete('123456789')

    def test_has_node_true(self):
        self.nodedb.insert('123456789', 'test')
        self.assertTrue(self.nodedb.has_node('123456789'))

    def test_has_node_false(self):
        self.assertFalse(self.nodedb.has_node('123456789'))




if __name__ == '__main__':
    unittest.main()
