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

class TestDefinition(unittest.TestCase):
    #pylint: disable=R0904

    def __init__(self, node):
        super(TestDefinition, self).__init__('run_test')
        self.node = node
        self.neighbordb_node = ztpserver.topology.create_node(node['details'])

    def run_test(self):
        print 'Checking node: %s' % self.node['node']
        result = ztpserver.topology.neighbordb.match_node(self.neighbordb_node)

        if self.node['matches']:
            self.assertEqual(len(result), self.node['matches'])

        if self.node['match_includes']:
            matches = [x.name for x in result]
            self.assertEqual(matches, self.node['match_includes'])

        if self.node['match_excludes']:
            matches = [x.name for x in result]
            for match in self.node['match_excludes']:
                self.assertNotIn(match, matches)

def load_tests(_, _, _):
    suite = unittest.TestSuite()
    for test in [f for f in os.listdir('test/neighbordb') 
                 if os.path.join('test/neighbordb', f).endswith('_test')]:
        print 'Stating test %s' % test

        definition = yaml.load(open(os.path.join('test/neighbordb', test)))
        ztpserver.topology.clear()        
        ztpserver.topology.neighbordb.deserialize(definition['neighbordb'])

        for node in definition['nodes']:
            print 'Adding test: %s' % node['node']
            suite.addTest(TestDefinition(node))

    return suite

if __name__ == '__main__':
    unittest.main()
