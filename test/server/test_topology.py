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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
import unittest
import traceback

from mock import Mock

import ztpserver.serializers
import ztpserver.topology

from ztpserver.app import enable_handler_console    # pylint: disable=W0611
from ztpserver.topology import Pattern, PatternError
from ztpserver.topology import Topology, TopologyError
from ztpserver.topology import Node, NodeError

from server_test_lib import random_string
from server_test_lib import create_node, create_neighbordb, create_pattern


class NodeUnitTests(unittest.TestCase):

    def test_create_node_success(self):
        node = create_node()
        systemmac = node.systemmac
        kwargs = node.as_dict()
        del kwargs['systemmac']
        node = Node(systemmac, **kwargs)
        self.assertEqual(node.systemmac, systemmac)

    def test_create_node_systemmac_only(self):
        systemmac = random_string()
        node = Node(systemmac)
        self.assertEqual(node.systemmac, systemmac)

    def test_create_node_failure(self):
        try:
            node = Node()
        except TypeError:
            pass
        except Exception:
            self.fail()

    def test_create_node_neighbors_valid(self):
        systemmac = random_string()
        nodeattrs = create_node()

        device = random_string()
        port = random_string()

        neighbors = {'Ethernet1': {'device': device, 'port': port}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        del kwargs['systemmac']

        node = Node(systemmac, **kwargs)

        self.assertEqual(node.systemmac, systemmac)
        self.assertIsNotNone(node.neighbors('Ethernet1'))
        self.assertEqual(node.neighbors('Ethernet1')[0].device, device)
        self.assertEqual(node.neighbors('Ethernet1')[0].port, port)

    def test_create_node_neighbors_port_missing(self):
        systemmac = random_string()
        nodeattrs = create_node()

        device = random_string()

        neighbors = {'Ethernet1': {'device': device}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        del kwargs['systemmac']

        try:
            node = None
            node = Node(systemmac, **kwargs)
        except NodeError:
            pass
        except Exception as exc:
            self.fail(exc)
        finally:
            self.assertIsNone(node)

    def test_create_node_neighbors_device_missing(self):
        systemmac = random_string()
        nodeattrs = create_node()

        port = random_string()

        neighbors = {'Ethernet1': {'port': port}}
        nodeattrs.add_neighbors(neighbors)

        kwargs = nodeattrs.as_dict()
        del kwargs['systemmac']

        try:
            node = None
            node = Node(systemmac, **kwargs)
        except NodeError:
            pass
        except Exception as exc:
            self.fail(exc)
        finally:
            self.assertIsNone(node)

    def test_add_neighbor(self):
        systemmac = random_string()
        peer = Mock()
        intf = random_string()

        node = Node(systemmac)
        node.add_neighbor(intf, [dict(device=peer.device, port=peer.port)])

        self.assertIsNotNone(node.neighbors(intf))
        self.assertEqual(node.neighbors(intf)[0].device, peer.device)
        self.assertEqual(node.neighbors(intf)[0].port, peer.port)

    def test_add_neighbor_existing_interface(self):
        systemmac = random_string()
        peer = Mock()
        intf = random_string()

        node = Node(systemmac)
        node.add_neighbor(intf, [dict(device=peer.device, port=peer.port)])
        self.assertRaises(ztpserver.topology.NodeError, node.add_neighbor,
                          intf, [dict(device=peer.device, port=peer.port)])

    def test_add_neighbors_success(self):
        systemmac = random_string()
        nodeattrs = create_node()

        device = random_string()
        port = random_string()
        neighbors = {'Ethernet1': [{'device': device, 'port': port}]}

        kwargs = nodeattrs.as_dict()
        del kwargs['systemmac']

        node = Node(systemmac, **kwargs)
        node.add_neighbors(neighbors)

        self.assertEqual(node.systemmac, systemmac)
        self.assertIsNotNone(node.neighbors('Ethernet1'))
        self.assertEqual(node.neighbors('Ethernet1')[0].device, device)
        self.assertEqual(node.neighbors('Ethernet1')[0].port, port)

    def test_serialize_success(self):
        nodeattrs = create_node()
        systemmac = nodeattrs.systemmac
        kwargs = nodeattrs.as_dict()
        del kwargs['systemmac']
        node = Node(systemmac, **kwargs)
        result = node.serialize()
        self.assertEqual(result, nodeattrs.as_dict())


# class ResourcePoolUnitTests(unittest.TestCase):

#     def setUp(self):
#         self.pool = ResourcePool()

#         self.pool.load_from_file = Mock()
#         self.pool.dump_to_file = Mock()

#         self.pooldata = dict()
#         for i in range(0, 10):      # pylint: disable=W0612
#             self.pooldata[random_string()] = None
#         self.pool.data = self.pooldata

#     def test_serialize_success(self):
#         resp = self.pool.serialize()
#         self.assertEqual(resp, self.pool.data)

#     def test_deserialize_success(self):
#         pooldata = dict()
#         for i in range(0, 10):      # pylint: disable=W0612
#             pooldata[random_string()] = None
#         self.pool.deserialize(pooldata)
#         self.assertEqual(pooldata, self.pool.data)

#     def test_allocate_success(self):
#         node = create_node()
#         resp = self.pool.allocate(random_string(), node)
#         self.assertIsNotNone(resp)
#         self.assertIn(resp, self.pooldata.keys())

#     def test_allocate_success_existing(self):
#         node = create_node()
#         key = random_string()
#         self.pool.data[key] = node.systemmac
#         resp = self.pool.allocate(random_string(), node)
#         self.assertIsNotNone(resp)
#         self.assertIn(resp, key)

#     def test_allocate_success_no_resource(self):
#         node = create_node()
#         key = random_string()
#         for key in self.pool.data.keys():
#             self.pool.data[key] = random_string()

#         self.assertRaises(ResourcePoolError, self.pool.allocate,
#                           random_string(), node)

#     def test_lookup_success_found_key(self):
#         node = create_node()
#         key = random_string()
#         self.pool.data[key] = node.systemmac
#         resp = self.pool.lookup(random_string(), node)
#         self.assertEqual(resp, key)

#     def test_lookup_success_no_key(self):
#         node = create_node()
#         resp = self.pool.lookup(random_string(), node)
#         self.assertIsNone(resp)


class FunctionsUnitTests(unittest.TestCase):

    def test_exactfunction_true(self):
        value = random_string()
        func = ztpserver.topology.ExactFunction(value)
        self.assertTrue(func.match(value))

    def test_exactfunction_false(self):
        value = random_string()
        func = ztpserver.topology.ExactFunction(value)
        self.assertFalse(func.match(random_string()))

    def test_includesfunction_true(self):
        value = random_string()
        func = ztpserver.topology.IncludesFunction(value)
        self.assertTrue(func.match(value))

    def test_includesfunction_false(self):
        value = random_string()
        func = ztpserver.topology.IncludesFunction(value)
        self.assertFalse(func.match(random_string()))

    def test_excludesfunction_true(self):
        value = random_string()
        func = ztpserver.topology.ExcludesFunction(value)
        self.assertTrue(func.match(random_string()))

    def test_excludesfunction_false(self):
        value = random_string()
        func = ztpserver.topology.ExcludesFunction(value)
        self.assertFalse(func.match(value))

    def test_regexfunction_true(self):
        value = '[\w+]'
        func = ztpserver.topology.RegexFunction(value)
        self.assertTrue(func.match(random_string()))

    def test_regexfunction_false(self):
        value = '[^a-zA-Z0-9]'
        func = ztpserver.topology.RegexFunction(value)
        self.assertFalse(func.match(random_string()))


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


class PatternUnitTests(unittest.TestCase):

    def test_add_interface_success(self):
        kwargs = dict(name=random_string(),
              definition=random_string(),
              interfaces=None)

        pattern = Pattern(**kwargs)

        remote_device = random_string()
        remote_intf = random_string()
        neighbors = dict(Ethernet1={'device': remote_device,
                                    'port': remote_intf})

        try:
            pattern.add_interface(neighbors)
        except Exception as exc:
            print traceback.print_exc(exc)
            self.fail('add_interface raised an exception unexpectedly')


    def test_add_interface_failure(self):
        kwargs = dict(name=random_string(),
                      definition=random_string(),
                      interfaces=None)

        pattern = Pattern(**kwargs)
        self.assertRaises(PatternError, pattern.add_interface, random_string())


class TestInterfacePattern(unittest.TestCase):

    def test_create_interface_pattern(self):
        intf = random_string()
        device = random_string()
        port = random_string()

        obj = ztpserver.topology.InterfacePattern(intf, device, port)
        reprobj = 'InterfacePattern(interface=%s, device=%s, port=%s)' % \
                  (intf, device, port)
        self.assertEqual(repr(obj), reprobj)

    def test_match_success(self):
        interface = random_string()
        device = random_string()
        port = random_string()
        neighbors = [dict(device=device, port=port)]

        pattern = ztpserver.topology.InterfacePattern(interface, device, port)
        pattern.match_neighbors = Mock(return_value=True)
        pattern.match_interface = Mock(return_value=True)

        neighbor = ztpserver.topology.Neighbor(device, port)
        result = pattern.match(interface, neighbor)
        self.assertTrue(result)

    def test_match_false_interface(self):
        interface = random_string()
        device = random_string()
        port = random_string()
        neighbors = [dict(device=device, port=port)]

        pattern = ztpserver.topology.InterfacePattern(interface, device, port)
        pattern.match_neighbors = Mock(return_value=True)
        pattern.match_interface = Mock(return_value=False)

        neighbor = ztpserver.topology.Neighbor(device, port)
        result = pattern.match(interface, neighbor)

        self.assertFalse(pattern.match_neighbors.called)
        self.assertFalse(result)

    def test_match_false_neighbor(self):
        interface = random_string()
        device = random_string()
        port = random_string()
        neighbors = [dict(device=device, port=port)]

        pattern = ztpserver.topology.InterfacePattern(interface, device, port)
        pattern.match_neighbors = Mock(return_value=False)
        pattern.match_interface = Mock(return_value=True)

        neighbor = ztpserver.topology.Neighbor(device, port)

        self.assertRaises(ztpserver.topology.InterfacePatternError,
                          pattern.match, interface, neighbor)


    def compile_known_function(self, interface, cls):
        pattern = ztpserver.topology.InterfacePattern(interface,
                                                      random_string(),
                                                      random_string())
        self.assertIsInstance(pattern.interface_re, cls)

    def test_compile_exact_function(self):
        interface = 'exact(\'%s\')' % random_string()
        self.compile_known_function(interface, ztpserver.topology.ExactFunction)

    def test_compile_includes_function(self):
        interface = 'includes(\'%s\')' % random_string()
        self.compile_known_function(interface,
                                    ztpserver.topology.IncludesFunction)

    def test_compile_excludes_function(self):
        interface = 'excludes(\'%s\')' % random_string()
        self.compile_known_function(interface,
                                    ztpserver.topology.ExcludesFunction)

    def test_compile_regex_function(self):
        interface = 'regex(\'%s\')' % random_string()
        self.compile_known_function(interface,
                                    ztpserver.topology.RegexFunction)

    def test_compile_no_function(self):
        interface = random_string()
        self.compile_known_function(interface,
                                    ztpserver.topology.ExactFunction)

    def test_compile_unknown_function(self):
        interface = '%s(\'%s\')' % (random_string(), random_string())
        device = random_string()
        port = random_string()

        self.assertRaises(ztpserver.topology.InterfacePatternError,
                          ztpserver.topology.InterfacePattern,
                          interface, random_string(), random_string())

if __name__ == '__main__':
    unittest.main()
