#!/usr/bin/env python
#
# Copyright (c) 2015, Arista Networks, Inc.
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

#pylint: disable=R0904,F0401,W0232,E1101,W0402

import os
import os.path
import unittest
import sys
from string import Template

sys.path.append('test/client')

from client_test_lib import Bootstrap, ActionFailureTest
from client_test_lib import file_log, get_action, random_string
from client_test_lib import startup_config_action
from client_test_lib import raise_exception

class FailureTest(ActionFailureTest):

    def test_missing_url(self):
        self.basic_test('add_config', 'Missing attribute(\'url\')')

    def test_url_failure(self):
        self.basic_test('add_config', 'Unable to retrieve config from URL',
                        attributes={'url' :
                                    random_string()})

    def test_variables_failure(self):
        url = random_string()
        contents = random_string()
        self.basic_test('add_config', 
                        'Unable to perform variable substitution - '
                        'invalid variables',
                        attributes={'url' : url,
                                    'variables' : random_string()},
                        file_responses={url : contents})

    def test_variable_missing_failure(self):
        url = random_string()
        contents = random_string() + ' $missing_var'
        self.basic_test('add_config', 
                        'Unable to perform variable substitution - '
                        '\'missing_var\' missing from list of substitutions',
                        attributes={'url' : url,
                                    'substitution_mode': 'strict',
                                    'variables' : {}},
                        file_responses={url : contents})

    def test_invalid_substitution_mode(self):
        self.basic_test('add_config', 
                        'Invalid option specified for '
                        'substitution_mode attribute',
                        attributes={'url': random_string(),
                                    'substitution_mode': 'dummy'})


class SuccessTest(unittest.TestCase):


    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = config
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action',
                      'attributes': {'url' : url}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            self.failUnless(contents.split() == 
                            file_log(bootstrap.startup_config))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_success_url(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action',
                      'attributes': {'url' : url}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            self.failUnless(contents.split() == 
                            file_log(bootstrap.startup_config))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_append(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes': {'url' : url}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))

        startup_config_text = random_string()
        bootstrap.ztps.set_action_response(
            'startup_config_action',
            startup_config_action(lines=[startup_config_text]))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            log = file_log(bootstrap.startup_config)
            self.failUnless(contents in log)
            self.failUnless(startup_config_text in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_multi_lines(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes': {'url' : url}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))

        startup_config_lines = [random_string(), random_string(),
                                random_string(), random_string()]
        bootstrap.ztps.set_action_response(
            'startup_config_action',
            startup_config_action(lines=startup_config_lines))
        contents = '\n'.join([random_string(), random_string(),
                              random_string(), random_string(),
                              random_string(), random_string()])
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            log = file_log(bootstrap.startup_config)
            all_lines = startup_config_lines + contents.split()
            for line in all_lines:
                self.failUnless(line in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_variables_strict(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = config
        var_dict = { 'a' : 'A',
                     'b' : 'A',
                     'xxx' : '999',
                     'dummy': 'DUMMY'}
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action',
                      'attributes': {'url' : url,
                                     'substitution_mode': 'strict',
                                     'variables': var_dict}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = '$a 1234 $b 4  321 $xxx$a'
        expected_contents = Template(contents).substitute(var_dict)
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            self.failUnless([expected_contents] ==
                            file_log(bootstrap.startup_config))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_variables_loose(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = config
        var_dict = { 'a' : 'A',
                     'b' : 'A',
                     'xxx' : '999',
                     'dummy': 'DUMMY'}
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action',
                      'attributes': {'url' : url,
                                     'substitution_mode': 'loose',
                                     'variables': var_dict}}])
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = '$a 1234 $b 4  321 $xxx$a'
        expected_contents = Template(contents).safe_substitute(var_dict)
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(bootstrap.startup_config))
            self.failUnless([expected_contents] ==
                            file_log(bootstrap.startup_config))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

if __name__ == '__main__':
    unittest.main()
