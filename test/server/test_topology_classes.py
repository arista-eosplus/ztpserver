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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=W0142
#
import unittest

from mock import Mock

from ztpserver.app import enable_handler_console    # pylint: disable=W0611
from ztpserver.topology import InterfacePattern, InterfacePatternError
from ztpserver.topology import Pattern, PatternError
from ztpserver.topology import Node, NodeError, Neighbor

from ztpserver.topology import ExcludesFunction, IncludesFunction
from ztpserver.topology import ExactFunction, RegexFunction

from server_test_lib import random_string, enable_logging
from server_test_lib import create_node


class NodeUnitTests(unittest.TestCase):

    def test_create_node_success(self):
        node = create_node()
        systemmac = node.systemmac
        kwargs = node.as_dict()
        node = Node(**kwargs)
        self.assertEqual(node.systemmac, systemmac)

    def test_create_node_systemmac_only(self):
        systemmac = random_string()
        node = Node(systemmac=systemmac)
        self.assertEqual(node.systemmac, systemmac)

    @classmethod
    def test_create_node_failure(cls):
        try:
            _ = Node()
        except TypeError:
            pass

    def test_create_node_neighbors_valid(self):
        nodeattrs = create_node()

        remote_device = random_string()
        remote_interface = random_string()

        neighbors = {'Ethernet1': {'device': remote_device, 
                                   'port': remote_interface}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        node = Node(**kwargs)

        self.assertIsNotNone(node.neighbors('Ethernet1'))
        self.assertEqual(node.neighbors('Ethernet1')[0].device, 
                         remote_device)
        self.assertEqual(node.neighbors('Ethernet1')[0].interface, 
                         remote_interface)

    def test_create_node_neighbors_remote_interface_missing(self):
        nodeattrs = create_node()

        remote_device = random_string()

        neighbors = {'Ethernet1': {'remote_device': remote_device}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        try:
            node = None
            node = Node(**kwargs)
        except NodeError:
            pass
        finally:
            self.assertIsNone(node)

    def test_create_node_neighbors_remote_device_missing(self):
        nodeattrs = create_node()

        remote_interface = random_string()

        neighbors = {'Ethernet1': {'remote_interface': remote_interface}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        try:
            node = None
            node = Node(**kwargs)
        except NodeError:
            pass
        finally:
            self.assertIsNone(node)

    def test_add_neighbor(self):
        systemmac = random_string()
        peer = Mock()
        intf = random_string()

        node = Node(systemmac=systemmac)
        node.add_neighbor(intf, [dict(device=peer.remote_device, 
                                      port=peer.remote_interface)])

        self.assertIsNotNone(node.neighbors(intf))

        self.assertEqual(node.neighbors(intf)[0].device, 
                         peer.remote_device)
        self.assertEqual(node.neighbors(intf)[0].interface, 
                         peer.remote_interface)

    def test_add_neighbor_existing_interface(self):
        systemmac = random_string()
        peer = Mock()
        intf = random_string()

        node = Node(systemmac=systemmac)
        node.add_neighbor(intf, [dict(device=peer.remote_device, 
                                      port=peer.remote_interface)])
        self.assertRaises(NodeError, node.add_neighbor,
                          intf, [dict(device=peer.remote_device, 
                                      port=peer.remote_interface)])

    def test_add_neighbors_success(self):
        nodeattrs = create_node()

        remote_device = random_string()
        remote_interface = random_string()
        neighbors = {'Ethernet1': [{'device': remote_device, 
                                    'port': remote_interface}]}

        kwargs = nodeattrs.as_dict()
        node = Node(**kwargs)
        node.add_neighbors(neighbors)

        self.assertIsNotNone(node.neighbors('Ethernet1'))
        self.assertEqual(node.neighbors('Ethernet1')[0].device, 
                         remote_device)
        self.assertEqual(node.neighbors('Ethernet1')[0].interface, 
                         remote_interface)

    def test_serialize_success(self):
        nodeattrs = create_node()
        kwargs = nodeattrs.as_dict()
        node = Node(**kwargs)
        result = node.serialize()
        self.assertEqual(result, nodeattrs.as_dict())


class FunctionsUnitTests(unittest.TestCase):

    def test_exactfunction_true(self):
        value = random_string()
        func = ExactFunction(value)
        self.assertTrue(func.match(value))

    def test_exactfunction_false(self):
        value = random_string()
        func = ExactFunction(value)
        self.assertFalse(func.match(random_string()))

    def test_includesfunction_true(self):
        value = random_string()
        func = IncludesFunction(value)
        self.assertTrue(func.match(value))

    def test_includesfunction_false(self):
        value = random_string()
        func = IncludesFunction(value)
        self.assertFalse(func.match(random_string()))

    def test_excludesfunction_true(self):
        value = random_string()
        func = ExcludesFunction(value)
        self.assertTrue(func.match(random_string()))

    def test_excludesfunction_false(self):
        value = random_string()
        func = ExcludesFunction(value)
        self.assertFalse(func.match(value))

    def test_regexfunction_true(self):
        value = r'[\w+]'
        func = RegexFunction(value)
        self.assertTrue(func.match(random_string()))

    def test_regexfunction_false(self):
        value = '[^a-zA-Z0-9]'
        func = RegexFunction(value)
        self.assertFalse(func.match(random_string()))


class TestPattern(unittest.TestCase):

    def test_create_pattern_with_defaults(self):
        obj = Pattern(None, None, None)
        self.assertIsInstance(obj, Pattern)

    def test_create_pattern_with_kwargs(self):
        obj = Pattern(name='test',
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
        obj = Pattern(interfaces=[{'Ethernet1': 'any'}])
        self.assertEqual(len(obj.interfaces), 1)


class PatternUnitTests(unittest.TestCase):

    def test_create_pattern(self):
        pattern = Pattern(random_string())
        self.assertIsInstance(pattern, Pattern)

    def test_create_pattern_kwargs(self):
        kwargs = dict(name=random_string(),
                      definition=random_string(),
                      interfaces=None)

        pattern = Pattern(**kwargs)
        self.assertIsInstance(pattern, Pattern)

    @classmethod
    def test_add_interface_success(cls):
        kwargs = dict(name=random_string(),
                      definition=random_string(),
                      interfaces=None)

        pattern = Pattern(**kwargs)

        remote_remote_device = random_string()
        remote_intf = random_string()
        neighbors = dict(Ethernet1={'device': remote_remote_device,
                                    'port': remote_intf})

        pattern.add_interface(neighbors)
            
    def test_add_interface_failure(self):
        kwargs = dict(name=random_string(),
                      definition=random_string(),
                      interfaces=None)

        pattern = Pattern(**kwargs)
        self.assertRaises(PatternError, pattern.add_interface, 
                          random_string())


class TestInterfacePattern(unittest.TestCase):

    def test_create_interface_pattern(self):
        intf = 'Ethernet1'
        remote_device = random_string()
        remote_interface = random_string()

        obj = InterfacePattern(intf, remote_device,
                               remote_interface,
                               random_string())
        reprobj = 'InterfacePattern(interface=%s, remote_device=%s, ' \
                   'remote_interface=%s)' % \
                  (intf, remote_device, remote_interface)
        self.assertEqual(repr(obj), reprobj)

    def test_match_success(self):
        interface = random_string()
        remote_device = random_string()
        remote_interface = random_string()

        neighbor = Neighbor(remote_device, remote_interface)
        for intf in ['any', interface]:
            for remote_d in ['any', remote_device]:
                for remote_i in ['any', remote_interface]:
                    
                    pattern = InterfacePattern(intf, remote_d, remote_i,
                                               random_string())
                    result = pattern.match(interface, [neighbor])
                    self.assertTrue(result)

    def test_match_failure(self):
        interface = random_string()
        remote_device = random_string()
        remote_interface = random_string()

        for intf in ['none', interface + 'dummy']:
            pattern = InterfacePattern(intf, remote_device, 
                                       remote_interface,
                                       random_string())
            neighbor = Neighbor(remote_device, remote_interface)
            result = pattern.match(interface, [neighbor])
            self.assertFalse(result)

        for remote_d in ['none', remote_device + 'dummy']:
            pattern = InterfacePattern(interface, remote_d, 
                                       remote_interface,
                                       random_string())
            neighbor = Neighbor(remote_device, remote_interface)
            result = pattern.match(interface, [neighbor])
            self.assertFalse(result)

        for remote_i in ['none', remote_interface + 'dummy']:
            pattern = InterfacePattern(interface, remote_device, 
                                       remote_i, random_string())
            neighbor = Neighbor(remote_device, remote_interface)
            result = pattern.match(interface, [neighbor])
            self.assertFalse(result)

        for remote_d in ['none', remote_device + 'dummy']:
            for remote_i in ['none', remote_interface + 'dummy']:
                pattern = InterfacePattern(interface, remote_d, 
                                           remote_i, random_string())
                neighbor = Neighbor(remote_device, remote_interface)
                result = pattern.match(interface, [neighbor])
                self.assertFalse(result)

        for intf in ['none', interface + 'dummy']:
            for remote_i in ['none', remote_interface + 'dummy']:
                pattern = InterfacePattern(intf, remote_device, 
                                           remote_i, random_string())
                neighbor = Neighbor(remote_device, remote_interface)
                result = pattern.match(interface, [neighbor])
                self.assertFalse(result)

        for intf in ['none', interface + 'dummy']:
            for remote_d in ['none', remote_device + 'dummy']:
                pattern = InterfacePattern(intf, remote_d, 
                                           remote_interface, random_string())
                neighbor = Neighbor(remote_device, remote_interface)
                result = pattern.match(interface, [neighbor])
                self.assertFalse(result)

        for intf in ['none', interface + 'dummy']:
            for remote_d in ['none', remote_device + 'dummy']:
                for remote_i in ['none', remote_interface + 'dummy']:
                    pattern = InterfacePattern(intf, remote_d, 
                                               remote_i, random_string())
                    neighbor = Neighbor(remote_device, remote_interface)
                    result = pattern.match(interface, [neighbor])
                    self.assertFalse(result)

    def compile_known_function(self, interface, cls):
        pattern = InterfacePattern(random_string(),
                                   interface,
                                   random_string(),
                                   random_string())
        self.assertIsInstance(pattern.remote_device_re, cls)

    def test_compile_exact_function(self):
        interface = 'exact(\'%s\')' % random_string()
        self.compile_known_function(interface, ExactFunction)

    def test_compile_includes_function(self):
        interface = 'includes(\'%s\')' % random_string()
        self.compile_known_function(interface, IncludesFunction)

    def test_compile_excludes_function(self):
        interface = 'excludes(\'%s\')' % random_string()
        self.compile_known_function(interface, ExcludesFunction)

    def test_compile_regex_function(self):
        interface = 'regex(\'%s\')' % random_string()
        self.compile_known_function(interface, RegexFunction)

    def test_compile_no_function(self):
        interface = random_string()
        self.compile_known_function(interface, ExactFunction)

    def test_compile_unknown_function(self):
        interface = '%s(\'%s\')' % (random_string(), random_string())
        self.assertRaises(InterfacePatternError,
                          InterfacePattern,
                          random_string(), interface,
                          random_string(), random_string())

if __name__ == '__main__':
    enable_logging()
    unittest.main()
