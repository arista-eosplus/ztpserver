import unittest

import yaml

import ztpserver.neighbordb

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

        ztpserver.neighbordb.topology.deserialize(self.neighbordb)
        print 'INFO: NeighborDB: %r' % ztpserver.neighbordb.topology
        self.longMessage = True

    def run_test(self):
        #print 'Checking node: %s [%s]' % (self.node['node'], self.name)
        result = ztpserver.neighbordb.topology.match_node(self.neighbordb_node)
        result = [x.name for x in result]
        #print 'Result: %s' % result

        if self.node.get('matches', None):
            self.assertEqual(len(result), self.node['matches'],
                             'test \'matches\' failed for node %s [%s]' % \
                                (self.node['node'], self.name))

        if self.node.get('match_includes', None):
            self.assertEqual(result, self.node['match_includes'],
                             'test \'match_includes\' failed for node %s [%s]' % \
                                (self.node['node'], self.name))

        if self.node.get('match_excludes', None):
            for match in self.node['match_excludes']:
                self.assertNotIn(match, result,
                             'test \'match_excludes\' failed for node %s [%s]' % \
                                (self.node['node'], self.name))

