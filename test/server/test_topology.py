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
from ztpserver.topology import ResourcePool, ResourcePoolError
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
