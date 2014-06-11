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

import os
import unittest
import logging
import argparse

import yaml

from ztpserver.app import enable_handler_console
from ztpserver.neighbordb import load_topology, load_node
from ztpserver.validators import TopologyValidator

TEST_DIR = 'test/neighbordb'

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

def enable_logging(level=None):
    logging_fmt = '%(levelname)s: [%(module)s:%(lineno)d] %(message)s'
    formatter = logging.Formatter(logging_fmt)

    ch = logging.StreamHandler()
    ch.tag = 'console'
    level = level or 'DEBUG'
    level = str(level).upper()
    level = logging.getLevelName(level)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

class NeighbordbTest(unittest.TestCase):

    def __init__(self, test_name, ndb, **kwargs):
        self.ndb = ndb
        self.node = kwargs.get('node')
        self.tag = kwargs.get('tag')
        self.match = kwargs.get('match')

        self.valid_patterns = kwargs.get('valid_patterns', dict())
        if not self.valid_patterns.get('nodes'):
            self.valid_patterns['nodes'] = list()
        if not self.valid_patterns.get('globals'):
            self.valid_patterns['globals'] = list()

        self.failed_patterns = kwargs.get('failed_patterns')

        self.longMessage = True
        super(NeighbordbTest, self).__init__(test_name)

    def _load_topology(self):
        return load_topology(contents=self.ndb)

    def _validate_topology(self):
        validator = TopologyValidator()
        validator.validate(self.ndb)
        return (validator.valid_patterns,
                validator.failed_patterns,
                validator.messages)

    def neighbordb_pattern(self):
        log.info('START: neighbordb_patterns')
        tag = 'tag=%s' % self.tag

        (valid, failed, messages) = self._validate_topology()

        if self.failed_patterns:
            failed_names = sorted([p[1] for p in failed])
            self.assertEqual(failed_names, sorted(self.failed_patterns), tag)
            self.assertEqual(len(failed), len(self.failed_patterns), tag)

        p_all = self.valid_patterns.get('nodes') + \
                self.valid_patterns.get('globals')
        if p_all:
            valid_names = sorted([p[1] for p in valid])
            self.assertEqual(valid_names, sorted(p_all), tag)

        log.info('END: neighbordb_patterns')

    def neighbordb_topology(self):
        log.info('START: neighbordb_topology')
        tag = 'tag=%s' % self.tag

        topo = self._load_topology()
        self.assertIsNotNone(topo, tag)

        p_nodes = [p.name for p in topo.get_patterns(topo.isnodepattern)]
        p_globals = [p.name for p in topo.get_patterns(topo.isglobalpattern)]

        self.assertEqual(sorted(self.valid_patterns['nodes']),
                         sorted(p_nodes),
                         tag)
        self.assertEqual(sorted(self.valid_patterns['globals']),
                         sorted(p_globals),
                         tag)

        log.info('END: neighbordb_topology')
        return topo

    def node_pass(self):
        log.info('START: node_pass')
        tag = 'tag=%s' % self.tag

        node = load_node(self.node)
        self.assertIsNotNone(node, tag)

        topology = self._load_topology()
        result = topology.match_node(node)

        self.assertEqual(result[0].name, self.match, tag)
        self.assertTrue(result, tag)

        log.info('END: node_pass')

    def node_fail(self):
        log.info('START: node_fail')
        tag = 'tag=%s' % self.tag

        node = load_node(self.node)
        self.assertIsNotNone(node, tag)

        topology = self._load_topology()
        self.assertIsNotNone(topology, tag)

        result = topology.match_node(node)
        self.assertFalse(result, tag)

        log.info('END: node_fail')

def get_test_list(filepath):
    test_list = os.environ.get('TESTS', None)
    if not test_list:
        log.debug('Checking directory %s for tests', TEST_DIR)
        test_list = [os.path.join(filepath, f) for f in os.listdir(filepath)
                     if f.endswith('yml')]
    else:
        test_list = [os.path.join(filepath, f) for f in test_list.split(',')]
    return test_list

def load_tests(loader, tests, pattern):
    try:
        log.info('Start ndb tests')

        suite = unittest.TestSuite()
        test_list = get_test_list(TEST_DIR)
        log.info('Test list is %s', test_list)

        for test in test_list:
            log.info('Starting test harness %s', test)

            harness = yaml.load(open(test))
            if harness.get('debug'):
                enable_handler_console()

            tests = harness.get('tests', ['topology'])

            name = harness.get('ndb', 'neighbordb')
            fn = name.split('/')[-1]
            if fn in harness:
                ndb = harness.get(fn)
            else:
                assert os.path.exists(name)
                ndb = yaml.load(open(name))

            kwargs = dict()
            kwargs['valid_patterns'] = harness.get('valid_patterns', dict())
            kwargs['failed_patterns'] = harness.get('failed_patterns')
            kwargs['tag'] = harness.get('tag')

            for test in tests:
                assert test in ['pattern', 'topology']
                test_name = 'neighbordb_%s' % test
                suite.addTest(NeighbordbTest(test_name, ndb, **kwargs))

            if 'nodes' in harness and 'topology' in tests:
                for key in harness['nodes'].keys():
                    assert key in ['pass', 'fail']
                    test = 'node_%s' % key
                    entries = harness['nodes'][key]
                    if not entries is None:
                        for entry in entries:
                            fn = entry['name'].split('/')[-1]
                            kwargs['node'] = harness.get(fn, entry['name'])
                            kwargs['match'] = entry.get('match')
                            kwargs['tag'] = entry.get('tag', fn)
                            log.info('Adding node %s', name)
                            suite.addTest(NeighbordbTest(test, ndb, **kwargs))

    except Exception:
        log.exception('Unexpected error trying to execute load_tests')
    else:
        return suite

if __name__ == '__main__':
    #enable_logging()
    unittest.main()
