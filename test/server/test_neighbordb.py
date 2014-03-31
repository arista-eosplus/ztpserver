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
import os
import json
import unittest

import yaml

import ztpserver.topology

class NodeDefinition(object):

    def __init__(self, node, matches=None, match_includes=None,
                 match_excludes=None):
        self.filename = node
        self.data = self.load_node(node)
        self.matches = matches
        self.match_includes = match_includes
        self.match_excludes = match_excludes

    def load_node(self, filename):
        attrs = json.load(open(filename))
        return ztpserver.topology.create_node(attrs)


class TestDefinition(unittest.TestCase):

    def __init__(self, testname, neighbordb, node):
        super(TestDefinition, self).__init__(testname)
        self.neighbordb = neighbordb
        self.node = NodeDefinition(**node)

    def setUp(self):
        ztpserver.topology.load(self.neighbordb)
        self.longMessage = True

    def run_test(self):
        result = ztpserver.topology.neighbordb.match_node(self.node.data)

        if self.node.matches:
            self.assertEqual(len(result), self.node.matches, self.node.filename)

        if self.node.match_includes:
            matches = [x.name for x in result]
            self.assertEqual(matches, self.node.match_includes, self.node.filename)

        if self.node.match_excludes:
            matches = [x.name for x in result]
            for match in self.node.match_excludes:
                self.assertNotIn(match, matches, self.node.filename)


def get_dirs(dir=None):
    if not dir:
        dir = os.getcwd()
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    path = os.path.join(os.getcwd(), 'test/neighbordb')
    for folder in get_dirs(dir=path):
        fp = os.path.join(path, folder)

        definition = yaml.load(open(os.path.join(fp, 'test_definition')))
        neighbordb = os.path.join(fp, definition.get('neighbordb'))

        for node in definition.get('nodes'):
            node['node'] = os.path.join(fp, node['node'])
            suite.addTest(TestDefinition('run_test', neighbordb, node))

    return suite

if __name__ == "__main__":
    unittest.main()

