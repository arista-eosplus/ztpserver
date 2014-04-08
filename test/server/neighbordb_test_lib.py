# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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

import unittest

import ztpserver.neighbordb

class TestDefinition(unittest.TestCase):
    #pylint: disable=R0904,C0103

    def __init__(self, name, node, neighbordb):
        super(TestDefinition, self).__init__('run_test')
        self.name = name
        self.node = node
        self.neighbordb = neighbordb
        node_details = node['node']
        node_details['neighbors'] = node['neighbors']
        self.neighbordb_node = ztpserver.neighbordb.create_node(node_details)

    def setUp(self):
        ztpserver.neighbordb.topology.clear()

        assert not ztpserver.neighbordb.topology.patterns['globals']
        assert not ztpserver.neighbordb.topology.patterns['nodes']

        ztpserver.neighbordb.topology.deserialize(self.neighbordb)
        print 'INFO: NeighborDB: %r' % ztpserver.neighbordb.topology
        self.longMessage = True     # pylint: disable=C0103

    def run_test(self):
        print 'INFO: Checking node: %s [%s]' % (self.node['name'], self.name)
        result = ztpserver.neighbordb.topology.match_node(self.neighbordb_node)
        result = [x.name for x in result]
        print 'INFO: Matches Result: %s' % result

        expected_result = self.node['matches']
        if expected_result.get('includes', None):
            self.assertEqual(result, expected_result['includes'],
                             'test \'includes\' failed for node %s [%s]' % \
                                 (self.node['name'], self.name))

        if expected_result.get('excludes', None):
            for entry in expected_result['excludes']:
                self.assertNotIn(entry, result,
                                 'test \'excludes\' failed for node %s [%s]' % \
                                     (self.node['name'], self.name))

        if expected_result.get('count', 0):
            self.assertEqual(len(result), expected_result['count'],
                             'test \'count\' failed for node %s [%s]' % \
                                 (self.node['name'], self.name))
