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

import ztpserver.data

class Functions(unittest.TestCase):

    def setUp(self):
        self.Functions = ztpserver.data.Functions

    def test_functions_exact_true(self):
        self.assertTrue(self.Functions.exact('test', 'test'))

    def test_functions_exact_false(self):
        self.assertFalse(self.Functions.exact('test', 'nottest'))

    def test_functions_includes_true(self):
        self.assertTrue(self.Functions.includes('test', 'unittest'))

    def test_functions_includes_false(self):
        self.assertFalse(self.Functions.includes('test', 'functions'))

    def test_functions_excludes_true(self):
        self.assertTrue(self.Functions.excludes('test', 'functions'))

    def test_functions_includes_false(self):
        self.assertFalse(self.Functions.excludes('test', 'unittest'))

    def test_functions_regex_true(self):
        self.assertTrue(self.Functions.regex("\w+", "test"))

    def test_functions_regex_false(self):
        self.assertFalse(self.Functions.regex("\d+", "test"))

class TestNodeDb(unittest.TestCase):

    def test_nodedb_instance(self):
        obj = ztpserver.data.NodeDb()
        self.assertEqual(repr(obj), "NodeDb(entries=0)")

    def test_nodedb_load_valid(self):
        fn = os.path.join(os.getcwd(), "test/data/nodedb.yml")
        obj = ztpserver.data.NodeDb()
        obj.load(fn)
        self.assertEqual(repr(obj), "NodeDb(entries=6)")

    def test_nodedb_load_invalid(self):
        fn = os.path.join(os.getcwd(), "/tmp/path/to/invalid/file/nodedb.yml")
        obj = ztpserver.data.NodeDb()
        self.assertRaises(ztpserver.data.NodeDbError, obj.load, fn)

if __name__ == '__main__':
    unittest.main()
