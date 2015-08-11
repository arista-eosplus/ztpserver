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

# pylint: disable=W0142

import os
import unittest
import traceback
import yaml

from ztpserver.app import enable_handler_console
from ztpserver.topology import load_neighbordb, load_file
from ztpserver.topology import Node
from ztpserver.validators import NeighbordbValidator
from ztpserver.constants import CONTENT_TYPE_YAML
from server_test_lib import enable_logging, log, random_string

TEST_DIR = 'test/neighbordb'
ID = random_string()

def debug(exc):
    # Uncomment line for debugging
    # import pdb; pdb.set_trace()
    
    raise exc

def load_node(node, content_type=CONTENT_TYPE_YAML):
    try:
        if not hasattr(node, 'items'):
            node = load_file(node, content_type, ID)
        if 'systemmac' in node:
            for symbol in [':', '.']:
                node['systemmac'] = str(node['systemmac']).replace(symbol, '')
        return Node(**node)
    except TypeError:
        log.error('Failed to load node')
    except KeyError as err:
        log.error('Failed to load node - missing attribute: %s' % err)

class NeighbordbTest(unittest.TestCase):
    # pylint: disable=C0103

    def __init__(self, test_name, ndb, **kwargs):
        self.ndb = ndb
        self.node = kwargs.get('node')
        self.tag = kwargs.get('tag')
        self.match = kwargs.get('match')
        self.filename = kwargs.get('filename')

        self.valid_patterns = kwargs.get('valid_patterns', dict())
        if not self.valid_patterns.get('nodes'):
            self.valid_patterns['nodes'] = list()
        if not self.valid_patterns.get('globals'):
            self.valid_patterns['globals'] = list()

        self.invalid_patterns = kwargs.get('invalid_patterns')

        self.longMessage = True   
        self.maxDiff = None

        super(NeighbordbTest, self).__init__(test_name)

    def _load_neighbordb(self):
        return load_neighbordb(ID, contents=self.ndb)

    def _validate_neighbordb(self):
        validator = NeighbordbValidator(ID)
        validator.validate(self.ndb)
        return (validator.valid_patterns, validator.invalid_patterns)

    def neighbordb_pattern(self):
        try:
            log.info('START: neighbordb_patterns')
            tag = 'tag=%s, fn=%s' % (self.tag, self.filename)

            (valid, failed) = self._validate_neighbordb()

            if self.invalid_patterns:
                failed_names = sorted([p[1] for p in failed])
                self.assertEqual(failed_names, 
                                 sorted(self.invalid_patterns),
                                 tag)
                self.assertEqual(len(failed), len(self.invalid_patterns), tag)

            p_all = self.valid_patterns.get('nodes') + \
                    self.valid_patterns.get('globals')
            if p_all:
                valid_actual = sorted([str(p[1]) for p in valid])
                valid_configured = sorted([str(x) for x in p_all])

                self.assertEqual(valid_actual, valid_configured, tag)

            log.info('END: neighbordb_pattern')
        except AssertionError as exc:
            print exc
            print traceback.format_exc()
            debug(exc)

    def neighbordb_topology(self):
        try:
            log.info('START: neighbordb_test')
            tag = 'tag=%s, fn=%s' % (self.tag, self.filename)

            topo = self._load_neighbordb()
            self.assertIsNotNone(topo, tag)

            p_nodes = [p.name for p in topo.get_patterns() 
                       if topo.is_node_pattern(p)]
            p_globals = [p.name for p in topo.get_patterns()
                         if topo.is_global_pattern(p)]

            self.assertEqual(sorted(self.valid_patterns['nodes']),
                             sorted(p_nodes),
                             tag)
            self.assertEqual(sorted(self.valid_patterns['globals']),
                             sorted(p_globals),
                             tag)

            log.info('END: neighbordb_test')
            return topo
        except AssertionError as exc:
            print exc
            print traceback.format_exc()
            debug(exc)

    def node_pass(self):
        try:
            log.info('START: node_pass')
            tag = 'tag=%s, fn=%s' % (self.tag, self.filename)
            
            node = load_node(self.node)
            self.assertIsNotNone(node, tag)
            
            neighbordb = self._load_neighbordb()
            self.assertIsNotNone(neighbordb, tag)
            result = neighbordb.match_node(node)
            
            self.assertTrue(result, tag)
            self.assertEqual(result[0].name, self.match, tag)
            log.info('END: node_pass')
        except AssertionError as exc:
            print exc
            print traceback.format_exc()
            debug(exc)

    def node_fail(self):
        try:
            log.info('START: node_fail')
            tag = 'tag=%s, fn=%s' % (self.tag, self.filename)

            node = load_node(self.node)
            self.assertIsNotNone(node, tag)

            neighbordb = self._load_neighbordb()
            self.assertIsNotNone(neighbordb, tag)

            result = neighbordb.match_node(node)

            self.assertFalse(result, tag)
            log.info('END: node_fail')
        except AssertionError as exc:
            print exc
            print traceback.format_exc()
            debug(exc)


def get_test_list(filepath):
    test_list = os.environ.get('TESTS', None)
    if not test_list:
        log.debug('Checking directory %s for tests', TEST_DIR)
        test_list = [os.path.join(filepath, f) for f in os.listdir(filepath)
                     if f.endswith('yml')]
    else:
        test_list = [os.path.join(filepath, f) for f in test_list.split(',')]
    return test_list

def load_tests(loader, tests, pattern):      # pylint: disable=W0613
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
            filename = name.split('/')[-1]
            if filename in harness:
                ndb = harness.get(filename)
            else:
                assert os.path.exists(name)
                ndb = yaml.load(open(name))

            kwargs = dict()
            kwargs['valid_patterns'] = harness.get('valid_patterns', dict())
            kwargs['invalid_patterns'] = harness.get('invalid_patterns')
            kwargs['tag'] = harness.get('tag', filename)
            kwargs['filename'] = test

            for test in tests:
                assert test in ['pattern', 'topology']
                suite.addTest(NeighbordbTest('neighbordb_%s' % test, 
                                             ndb, **kwargs))

            if 'nodes' in harness and 'topology' in tests:
                for key in harness['nodes'].keys():
                    assert key in ['pass', 'fail']
                    entries = harness['nodes'][key]
                    if not entries is None:
                        for entry in entries:
                            filename = entry['name'].split('/')[-1]
                            kwargs['node'] = harness.get(filename, 
                                                         entry['name'])
                            kwargs['match'] = entry.get('match')
                            kwargs['tag'] = '%s:%s' % (harness.get('tag'), 
                                                       filename)
                            log.info('Adding node %s', name)
                            suite.addTest(NeighbordbTest('node_%s' % key, 
                                                         ndb, **kwargs))

    except Exception as exc:      # pylint: disable=W0703
        log.exception('Unexpected error trying to execute load_tests: %s' %
                      exc)
    else:
        return suite

if __name__ == '__main__':
    enable_logging()
    unittest.main()
