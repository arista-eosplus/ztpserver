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

#pylint: disable=R0904,F0401,W0232,E1101

import os
import os.path
import random
import unittest
import sys

sys.path.append('test/client')

from client_test_lib import debug    #pylint: disable=W0611
from client_test_lib import RC_EOS
from client_test_lib import Bootstrap, ActionFailureTest
from client_test_lib import file_log, get_action, random_string
from client_test_lib import startup_config_action, remove_file

class FailureTest(ActionFailureTest):

    def test_missing_src_url(self):
        self.basic_test('copy_file', 1)

    def test_missing_dst_url(self):
        self.basic_test('copy_file', 2,
                        attributes={'copy_file-src_url' : 
                                    random_string()})

    def test_wrong_overwrite_value(self):
        self.basic_test('copy_file', 3,
                        attributes={'copy_file-src_url' : 
                                    random_string(),
                                    'copy_file-dst_url' :
                                    random_string(),
                                    'copy_file-overwrite' :
                                    'bogus'})

    def test_url_failure(self):
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                '/tmp')

        self.basic_test('copy_file', 4,
                        attributes={'copy_file-src_url' : 
                                    random_string(),
                                    'copy_file-dst_url' :
                                    random_string()},
                        action_value=action)


class SuccessTest(unittest.TestCase):

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination_file = random_string()
        destination = '/%s/%s' % (random_string(), 
                                  destination_file)

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'name' : 'startup_config_action'},
                     {'name' : 'test_action'}],
            attributes={'copy_file-src_url' : url,
                        'copy_file-dst_url' : destination})

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        persistent_dir = '/tmp'
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                persistent_dir)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (persistent_dir,
                                      destination_file)

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] == 
                            file_log(destination_path))

            self.failUnless(os.path.isfile(RC_EOS))
            log = file_log(RC_EOS)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' % 
                            (destination_path, destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_replace(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination_file = random_string()
        destination = '/%s/%s' % (random_string(), 
                                  destination_file)

        url = 'http://%s/%s' % (bootstrap.server, source)
        attributes = {'copy_file-src_url' : url,
                      'copy_file-dst_url' : destination}

        # 'replace' is the default
        if bool(random.getrandbits(1)):
            attributes['copy_file-overwrite'] = 'replace'

        bootstrap.ztps.set_definition_response(
            actions=[{'name' : 'startup_config_action'},
                     {'name' : 'test_action'}],
            attributes=attributes)

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        persistent_dir = '/tmp'
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                persistent_dir)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (persistent_dir,
                                      destination_file)
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] == 
                            file_log(destination_path))

            self.failUnless(os.path.isfile(RC_EOS))
            log = file_log(RC_EOS)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' % 
                            (destination_path, destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_original(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination_file = random_string()
        destination = '/%s/%s' % (random_string(), 
                                  destination_file)

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'name' : 'startup_config_action'},
                     {'name' : 'test_action'}],
            attributes={'copy_file-src_url' : url,
                        'copy_file-dst_url' : destination,
                        'copy_file-overwrite' : 'keep-original'})

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        persistent_dir = '/tmp'
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                persistent_dir)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (persistent_dir,
                                      destination_file)
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] == 
                            file_log(destination_path))

            self.failUnless(os.path.isfile(RC_EOS))
            log = file_log(RC_EOS)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('[ ! -f %s ] && sudo cp %s %s' % 
                            (destination, destination_path, 
                             destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_backup(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination_file = random_string()
        destination = '/%s/%s' % (random_string(), 
                                  destination_file)

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'name' : 'startup_config_action'},
                     {'name' : 'test_action'}],
            attributes={'copy_file-src_url' : url,
                        'copy_file-dst_url' : destination,
                        'copy_file-overwrite' : 'backup'})

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        persistent_dir = '/tmp'
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                persistent_dir)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (persistent_dir,
                                      destination_file)
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] == 
                            file_log(destination_path))

            self.failUnless(os.path.isfile(RC_EOS))
            log = file_log(RC_EOS)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' % 
                            (destination_path, destination) in log)
            self.failUnless('[ -f %s ] && sudo mv %s %s.backup' %
                            (destination, destination, 
                             destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

if __name__ == '__main__':
    unittest.main()
