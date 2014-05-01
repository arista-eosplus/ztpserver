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

#pylint: disable=F0401,C0103

import unittest
import ztpserver.topology


class Functions(unittest.TestCase):

    def setUp(self):
        self.longMessage = True     # pylint: disable=C0103
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

    def test_functions_excludes_false(self):
        self.assertFalse(self.Functions.excludes('test', 'unittest'))

    def test_functions_regex_true(self):
        self.assertTrue(self.Functions.regex(r'\w+', 'test'))

    def test_functions_regex_false(self):
        self.assertFalse(self.Functions.regex(r'\d+', 'test'))


class TestNode(unittest.TestCase):

    def test_node_creation(self):
        obj = ztpserver.topology.Node('1234567890')
        self.assertEqual(obj.systemmac, '1234567890')
        self.assertEqual(repr(obj), 'Node(node=1234567890, '
                         'neighbors=OrderedCollection(), ...)')

    def test_node_creation_with_kwargs(self):
        obj = ztpserver.topology.Node(model='vEOS',
                                      systemmac='00:1c:73:aa:11:bb',
                                      serialnumber='0123456789',
                                      version='4.12.0')

        self.assertEqual(repr(obj), 'Node(node=00:1c:73:aa:11:bb, '
                         'neighbors=OrderedCollection(), ...)')
        self.assertEqual(obj.model, 'vEOS')
        self.assertEqual(obj.systemmac, '00:1c:73:aa:11:bb')
        self.assertEqual(obj.serialnumber, '0123456789')
        self.assertEqual(obj.version, '4.12.0')

    def test_node_add_neighbors_valid(self):
        obj = ztpserver.topology.Node('1234567890')
        obj.add_neighbors({'Ethernet': [{'device': 'test', 'port': 'test'}]})
        self.assertEqual(repr(obj), 'Node(node=1234567890, '
                         'neighbors=OrderedCollection([(\'Ethernet\', '
                         '[Neighbor(device=\'test\', port=\'test\')])]), '
                         '...)')
        self.assertIsNotNone(obj.neighbors('Ethernet'))


class TestPattern(unittest.TestCase):

    def test_create_pattern_with_defaults(self):
        obj = ztpserver.topology.Pattern(None, None, None)
        self.assertIsInstance(obj, ztpserver.topology.Pattern)

    def test_create_pattern_with_kwargs(self):
        obj = ztpserver.topology.Pattern(name='test',
                                         definition='test',
                                         node='abc123',
                                         variables={'var': 'test'},
                                         interfaces=[{'Ethernet1': 'any'}])
        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.definition, 'test')
        self.assertEqual(obj.node, 'abc123')
        self.assertDictEqual({'var': 'test'}, obj.variables)
        self.assertEqual(1, len(obj.interfaces))

    def test_add_interface(self):
        obj = ztpserver.topology.Pattern(None, None, [{'Ethernet1': 'any'}])
        self.assertEqual(len(obj.interfaces), 1)


class TestInterfacePattern(unittest.TestCase):
    #pylint: disable=W0142

    def test_create_interface_pattern(self):
        obj = ztpserver.topology.InterfacePattern('Ethernet1', 'any', 'any')
        reprobj = 'InterfacePattern(interface=Ethernet1, remote_device=any, '\
            'remote_interface=any, remote_device_init=any, '\
            'remote_interface_init=any)'
        self.assertEqual(repr(obj), reprobj)

    def remote_device_test(self, device_to_match, device, fail=False):
        obj = ztpserver.topology.InterfacePattern('Ethernet1',
                                                  device_to_match,
                                                  'any')
        neighbors = [ztpserver.topology.Neighbor(device, 'any')]
        try:
            self.assertTrue(obj.match_remote_device(neighbors))
            if fail:
                self.assertFalse('Erroneously matched %s to %s' %
                                 (device, obj))
        except AssertionError:
            if not fail:
                raise

    def test_match_device_exact_true(self):
        self.remote_device_test('exact("spine")', 'spine')

    def test_match_device_exact_false(self):
        self.remote_device_test('exact("spine")', 'leaf', 
                                fail=True)

    def test_match_device_includes_true(self):
        self.remote_device_test('includes("spine")', 'pod1-spine1')

    def test_match_device_includes_false(self):
        self.remote_device_test('includes("spine")', 'pod1-leaf1', 
                                fail=True)

    def test_match_device_excludes_true(self):
        self.remote_device_test('excludes("spine")', 'pod1-leaf1')

    def test_match_device_excludes_false(self):
        self.remote_device_test('excludes("spine")', 'pod1-spine1', 
                                fail=True)

    def test_match_device_regex_true(self):
        self.remote_device_test(r'regex("pod\d+-spine\d+")',
                               'pod1-spine1')

    def test_match_device_regex_false(self):
        self.remote_device_test(r'exact("pod\d+-spine\d+")',
                                'pod1-leaf1', fail=True)

    def remote_port_test(self, port_to_match, port, fail=False):
        obj = ztpserver.topology.InterfacePattern('Ethernet1',
                                                  'any',
                                                  port_to_match)
        neighbors = [ztpserver.topology.Neighbor('any', port)]
        try:
            self.assertTrue(obj.match_remote_interface(neighbors))
            if fail:
                self.assertFalse('Erroneously matched %s to %s' %
                                 (port, obj))
        except AssertionError:
            if not fail:
                raise

    def test_match_port_true(self):
        self.remote_port_test('Ethernet1', 'Ethernet1')

    def test_match_port_true_range(self):
        self.remote_port_test('regex("Ethernet[1-3]")', 'Ethernet1')

    def test_match_port_false(self):
        self.remote_port_test('Ethernet1', 'Ethernet2', fail=True)

if __name__ == '__main__':
    unittest.main()
