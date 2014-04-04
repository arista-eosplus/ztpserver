#!/usr/bin/env python
#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
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

import os
import unittest
import yaml

import ztpserver.topology  #pylint: disable=F0401
import ztpserver.neighbordb

TEST_DIR = 'test/neighbordb'

class TestDefinition(unittest.TestCase):
    #pylint: disable=R0904

    def __init__(self, name, node, neighbordb):
        super(TestDefinition, self).__init__('run_test')
        self.name = name
        self.node = node
        self.neighbordb = neighbordb
        self.neighbordb_node = ztpserver.neighbordb.create_node(node['details'])

    def setUp(self):
        ztpserver.neighbordb.topology.clear()

        assert not ztpserver.neighbordb.topology.patterns['globals']
        assert not ztpserver.neighbordb.topology.patterns['nodes']

        ztpserver.neighbordb.loads(self.neighbordb)
        self.longMessage = True

    def run_test(self):
        print 'Checking node: %s' % self.node['node']
        result = ztpserver.neighbordb.topology.match_node(self.neighbordb_node)
        result = [x.name for x in result]
        print 'Result: %s' % result

        if self.node.get('matches', None):
            self.assertEqual(len(result), self.node['matches'],
                             self.name)

        if self.node.get('match_includes', None):
            self.assertEqual(result, self.node['match_includes'],
                             self.name)

        if self.node.get('match_excludes', None):
            for match in self.node['match_excludes']:
                self.assertNotIn(match, result,
                                 self.name)

def load_tests(loader, tests, pattern):            #pylint: disable=W0613
    suite = unittest.TestSuite()
    for test in [f for f in os.listdir(TEST_DIR)
                 if os.path.join(TEST_DIR, f).endswith('_test')]:
        print 'Starting test %s' % test

        definition = yaml.load(open(os.path.join(TEST_DIR, test)))

        for node in definition['nodes']:
            print 'Adding test: %s' % node['node']
            suite.addTest(TestDefinition(test, node, definition['neighbordb']))

    return suite

if __name__ == '__main__':
    unittest.main()
