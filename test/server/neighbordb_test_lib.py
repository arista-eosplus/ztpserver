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
import json

import ztpserver.neighbordb     #pylint: disable=F0401

from ztpserver.topology import Topology
from ztpserver.serializers import loads

class NodeTest(unittest.TestCase):
    #pylint: disable=R0904,C0103

    def __init__(self, name, node, neighbordb):
        super(NodeTest, self).__init__('run_test')
        self.name = name
        self.node = node
        self.neighbordb = neighbordb
        node_details = node['node']
        node_details['neighbors'] = node['neighbors']
        self.neighbordb_node = ztpserver.neighbordb.create_node(node_details)

    def setUp(self):
        print '\n---Starting test: %ss---\n' % self.name
        self.topology = ztpserver.neighbordb.load_topology(contents=self.neighbordb)

        print 'INFO: NeighborDB: %r' % self.topology
        self.longMessage = True     # pylint: disable=C0103

    def run_test(self):
        print 'INFO: Checking node: %s [%s]' % (self.node['name'], self.name)
        result = self.topology.match_node(self.neighbordb_node)
        result = [x.name for x in result]
        print 'INFO: Matches Result: %s' % result.sort()

        expected_result = self.node['matches']
        if expected_result.get('includes', None):
            self.assertEqual(result, sorted(expected_result['includes']),
                             'test \'includes\' failed for node %s [%s]' % \
                                 (self.node['name'], self.name))

        if expected_result.get('excludes', None):
            not_result = sorted([x.name for x in
                                 self.topology.get_patterns()
                                 if x.name not in result])
            self.assertEqual(not_result, sorted(expected_result['excludes']),
                             'test \'excludes\' failed for node %s [%s]' % \
                                 (self.node['name'], self.name))

        if expected_result.get('count', 0):
            self.assertEqual(len(result), expected_result['count'],
                             'test \'count\' failed for node %s [%s]' % \
                                 (self.node['name'], self.name))

class NeighbordbTest(unittest.TestCase):
    #pylint: disable=R0904,C0103

    def __init__(self, name, neighbordb, result):
        super(NeighbordbTest, self).__init__('run_test')
        self.name = name
        self.neighbordb = neighbordb
        self.result = result

    def setUp(self):
        print '\n---Starting test: %ss---\n' % self.name
        self.topology = ztpserver.neighbordb.load_topology(contents=self.neighbordb)

        print 'INFO: NeighborDB: %r' % self.topology
        self.longMessage = True     # pylint: disable=C0103

    def run_test(self):
        print 'INFO: Checking neighbordb [%s]' % self.name

        if self.result.get('nodes', None):
            self.assertEqual(sorted(self.result['nodes']),
                             self.topology.get_patterns(self.topology.isnodepattern),
                             'failed to match node patterns [%s]' % self.name)

        if self.result.get('globals', None):
            self.assertEqual(sorted(self.result['globals']),
                             self.topology.get_patterns(self.topology.isglobalpattern),
                             'failed to match global patterns [%s]' % self.name)
