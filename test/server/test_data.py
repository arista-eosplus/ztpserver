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

class TestInterface(unittest.TestCase):

    def test_create_interface(self):
        obj = ztpserver.data.Interface('Ethernet')
        self.assertEqual(repr(obj), "Interface(name=Ethernet, neighbors=0)")

    def test_add_neighbor(self):
        obj = ztpserver.data.Interface('Ethernet')
        obj.add_neighbor('test_device', 'test_port')
        self.assertEqual(repr(obj), "Interface(name=Ethernet, neighbors=1)")

        neighbor = obj.neighbors[0]
        self.assertEqual(neighbor.device, 'test_device')
        self.assertEqual(neighbor.port, 'test_port')

class TestInterfaces(unittest.TestCase):

    def test_create_interfaces(self):
        obj = ztpserver.data.Interfaces()
        self.assertEqual(repr(obj), "Interfaces(count=0)")

    def test_add_interface_from_string(self):
        obj = ztpserver.data.Interfaces()
        obj.add_interface("Ethernet")
        self.assertEqual(repr(obj['Ethernet']),
                         "Interface(name=Ethernet, neighbors=0)")

    def test_add_interface_from_object_valid(self):
        intf = ztpserver.data.Interface('Ethernet')
        obj = ztpserver.data.Interfaces()
        obj.add_interface(intf)
        self.assertEqual(repr(obj['Ethernet']),
                         "Interface(name=Ethernet, neighbors=0)")

    def test_add_interface_from_object_invalid(self):
        intf = dict(name='Ethernet')
        obj = ztpserver.data.Interfaces()
        self.assertRaises(TypeError, obj.add_interface, intf)

class TestNode(unittest.TestCase):

    def test_node_creation(self):
        obj = ztpserver.data.Node()
        self.assertEqual(repr(obj), "Node(interfaces=0)")

    def test_node_creation_with_kwargs(self):
        kwargs = dict(model='vEOS',
                      systemmac='00:1c:73:aa:11:bb',
                      serialnumber='0123456789',
                      version='4.12.0')
        obj = ztpserver.data.Node(**kwargs)

        self.assertEqual(repr(obj), "Node(interfaces=0)")
        self.assertEqual(obj.model, 'vEOS')
        self.assertEqual(obj.systemmac, '00:1c:73:aa:11:bb')
        self.assertEqual(obj.serialnumber, '0123456789')
        self.assertEqual(obj.version, '4.12.0')

    def test_node_add_interface_valid(self):
        obj = ztpserver.data.Node()
        obj.add_interface('Ethernet')
        self.assertEqual(repr(obj), "Node(interfaces=1)")
        self.assertIsNotNone(obj.interfaces('Ethernet'))

    def test_node_add_interface_invalid(self):
        obj = ztpserver.data.Node()
        self.assertRaises(TypeError, obj.add_interface, 'test')

class TestNeighborDb(unittest.TestCase):

    def test_create_neighbordb(self):
        obj = ztpserver.data.NeighborDb()
        self.assertIsInstance(obj, ztpserver.data.NeighborDb)

    def test_load_valid_filename_and_contents(self):
        fn = os.path.join(os.getcwd(), "test/data/neighbordb.yml")
        obj = ztpserver.data.NeighborDb()
        obj.load(fn)
        self.assertEqual(repr(obj), "NeighborDb(globals=3, nodes=2)")

    def test_load_invalid_filename(self):
        obj = ztpserver.data.NeighborDb()
        self.assertRaises(IOError, obj.load, '/tmp/fake/file')

    def test_parse_interface_values(self):
        obj = ztpserver.data.NeighborDb()
        values = dict(device='device', port='port', tags='tags')
        result = obj._parse_interface('Ethernet', values)
        expected = ('Ethernet', 'device', 'port', 'tags')
        self.assertEqual(result, expected)

    def test_parse_interface_any(self):
        obj = ztpserver.data.NeighborDb()
        result = obj._parse_interface('Ethernet', 'any')
        expected = ('Ethernet', 'any', 'any', None)
        self.assertEqual(result, expected)

    def test_parse_interface_none(self):
        obj = ztpserver.data.NeighborDb()
        result = obj._parse_interface('Ethernet', 'none')
        expected = ('Ethernet', None, None, None)
        self.assertEqual(result, expected)



class TestPattern(unittest.TestCase):

    def test_create_pattern(self):
        obj = ztpserver.data.Pattern('test', 'test')
        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.definition, 'test')

    def test_create_pattern_with_kwargs(self):
        kwargs = dict(node='abc123',
                      variables={ 'var': 'test'},
                      interfaces={ 'Ethernet1': 'any' })

        obj = ztpserver.data.Pattern('test', 'test', **kwargs)
        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.definition, 'test')
        self.assertEqual(obj.node, 'abc123')
        self.assertDictEqual({'var': 'test'}, obj.variables)
        self.assertDictEqual({'Ethernet1': 'any'}, obj.interfaces)

    def test_add_interface(self):
        obj = ztpserver.data.Pattern('test', 'test')
        obj.add_interface('Ethernet', 'device', 'port')
        self.assertEqual(len(obj.interfaces), 1)


class TestInterfacePattern(unittest.TestCase):

    def test_create_interface_pattern(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "any", "any")
        self.assertEqual(repr(obj), "InterfacePattern(interface=Ethernet, node=any, port=any)")

    def test_match_interface_valid(self):
        obj = ztpserver.data.InterfacePattern("Ethernet1", "any", "any")
        result = obj.match_interfaces(['Ethernet1', 'Ethernet2'])
        self.assertListEqual(result, ['Ethernet1'])

    def test_match_interface_invalid(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "any", "any")
        result = obj.match_interfaces(['Ethernet1', 'Ethernet2'])
        self.assertIsNone(result)

    def test_match_device_exact_true(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "exact('spine')", "any")
        self.assertTrue(obj.match_device('spine'))

    def test_match_device_exact_false(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "exact('spine')", "any")
        self.assertFalse(obj.match_device('leaf'))

    def test_match_device_includes_true(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "includes('spine')", "any")
        self.assertTrue(obj.match_device('pod1-spine1'))

    def test_match_device_includes_false(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "includes('spine')", "any")
        self.assertFalse(obj.match_device('pod1-leaf1'))

    def test_match_device_excludes_true(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "excludes('spine')", "any")
        self.assertTrue(obj.match_device('pod1-leaf1'))

    def test_match_device_excludes_false(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "excludes('spine')", "any")
        self.assertFalse(obj.match_device('pod1-spine1'))

    def test_match_device_regex_true(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "regex('pod\d+-spine\d+')", "any")
        self.assertTrue(obj.match_device('pod1-spine1'))

    def test_match_device_regex_false(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "exact('pod\d+-spine\d+')", "any")
        self.assertFalse(obj.match_device('pod1-leaf1'))

    def test_match_port_true(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "any", "Ethernet1")
        self.assertTrue(obj.match_port('Ethernet1'))

    def test_match_port_true_range(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "any", "Ethernet1-3")
        self.assertTrue(obj.match_port('Ethernet1'))

    def test_match_port_false(self):
        obj = ztpserver.data.InterfacePattern("Ethernet", "any", "Ethernet1")
        self.assertFalse(obj.match_port('Ethernet2'))





if __name__ == '__main__':
    unittest.main()
