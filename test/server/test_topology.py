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

import ztpserver.topology

class Functions(unittest.TestCase):

    def setUp(self):
        self.Functions = ztpserver.topology.Functions

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

class TestNode(unittest.TestCase):

    def test_node_creation(self):
        obj = ztpserver.topology.Node('1234567890')
        self.assertEqual(obj.systemmac, '1234567890')
        self.assertEqual(repr(obj), "Node(neighbors=0)")

    def test_node_creation_with_kwargs(self):
        kwargs = dict(model='vEOS',
                      systemmac='00:1c:73:aa:11:bb',
                      serialnumber='0123456789',
                      version='4.12.0')
        obj = ztpserver.topology.Node(**kwargs)

        self.assertEqual(repr(obj), "Node(neighbors=0)")
        self.assertEqual(obj.model, 'vEOS')
        self.assertEqual(obj.systemmac, '00:1c:73:aa:11:bb')
        self.assertEqual(obj.serialnumber, '0123456789')
        self.assertEqual(obj.version, '4.12.0')

    def test_node_add_neighbors_valid(self):
        obj = ztpserver.topology.Node('1234567890')
        obj.add_neighbors({"Ethernet": [{"device": "test", "port": "test"}]})
        self.assertEqual(repr(obj), "Node(neighbors=1)")
        self.assertIsNotNone(obj.neighbors('Ethernet'))


class TestPattern(unittest.TestCase):

    def test_create_pattern_with_defaults(self):
        obj = ztpserver.topology.Pattern()
        self.assertIsInstance(obj, ztpserver.topology.Pattern)

    def test_create_pattern_with_kwargs(self):
        kwargs = dict(name='test',
                      definition='test',
                      node='abc123',
                      variables={'var': 'test'},
                      interfaces=[{'Ethernet1': 'any'}])

        obj = ztpserver.topology.Pattern(**kwargs)
        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.definition, 'test')
        self.assertEqual(obj.node, 'abc123')
        self.assertDictEqual({'var': 'test'}, obj.variables)
        self.assertEqual(1, len(obj.interfaces))

    def test_add_interface(self):
        obj = ztpserver.topology.Pattern()
        obj.add_interface('Ethernet1', 'device', 'port')
        self.assertEqual(len(obj.interfaces), 1)


class TestInterfacePattern(unittest.TestCase):

    def test_create_interface_pattern(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "any")
        reprobj = "InterfacePattern(interface=Ethernet1, device=any, port=any)"
        self.assertEqual(repr(obj), reprobj)

    def test_match_neighbors_valid(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "any")
        attrs = {
            "systemmac": "00:1c:73:00:00:00",
            "neighbors": {
                'Ethernet1': [{'device': 'test', 'port': 'test'}],
                'Ethernet2': [{'device': 'test', 'port': 'test'}]
            }
        }
        node = ztpserver.topology.Node(**attrs)
        result = obj.match_neighbors(node.neighbors, {})
        self.assertEqual(result, ['Ethernet1'])

    def test_match_neighbors_invalid(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "any")

        attrs = {
            "systemmac": "00:1c:73:00:00:00",
            "neighbors": {
                'Ethernet1': [{'device': 'test', 'port': 'test'}],
                'Ethernet2': [{'device': 'test', 'port': 'test'}]
            }
        }
        node = ztpserver.topology.Node(**attrs)
        result = obj.match_neighbors(node.neighbors, {})
        self.assertEqual(result, ['Ethernet1'])

    def test_match_device_exact_true(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "exact('spine')", "any")
        self.assertTrue(obj.match_device('spine'))

    def test_match_device_exact_false(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "exact('spine')", "any")
        self.assertFalse(obj.match_device('leaf'))

    def test_match_device_includes_true(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "includes('spine')", "any")
        self.assertTrue(obj.match_device('pod1-spine1'))

    def test_match_device_includes_false(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "includes('spine')", "any")
        self.assertFalse(obj.match_device('pod1-leaf1'))

    def test_match_device_excludes_true(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "excludes('spine')", "any")
        self.assertTrue(obj.match_device('pod1-leaf1'))

    def test_match_device_excludes_false(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "excludes('spine')", "any")
        self.assertFalse(obj.match_device('pod1-spine1'))

    def test_match_device_regex_true(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "regex('pod\d+-spine\d+')", "any")
        self.assertTrue(obj.match_device('pod1-spine1'))

    def test_match_device_regex_false(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "exact('pod\d+-spine\d+')", "any")
        self.assertFalse(obj.match_device('pod1-leaf1'))

    def test_match_port_true(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "Ethernet1")
        self.assertTrue(obj.match_port('Ethernet1'))

    def test_match_port_true_range(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "Ethernet1-3")
        self.assertTrue(obj.match_port('Ethernet1'))

    def test_match_port_false(self):
        obj = ztpserver.topology.InterfacePattern("Ethernet1", "any", "Ethernet1")
        self.assertFalse(obj.match_port('Ethernet2'))





if __name__ == '__main__':
    unittest.main()
