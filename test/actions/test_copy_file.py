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

#pylint: disable=R0904,F0401,W0232,E1101

import os
import os.path
import random
import shutil
import sys
import unittest

from stat import ST_MODE

sys.path.append('test/client')

from client_test_lib import Bootstrap, ActionFailureTest
from client_test_lib import file_log, get_action, random_string
from client_test_lib import startup_config_action, remove_file
from client_test_lib import raise_exception

def random_permissions():
    return '7%s%s' % ((random.choice([1, 2, 3, 4, 5, 6, 7]),
                       random.choice([1, 2, 3, 4, 5, 6, 7])))


class FailureTest(ActionFailureTest):

    def test_missing_src_url(self):
        self.basic_test('copy_file',
                        'Missing attribute(\'src_url\')')

    def test_missing_dst_url(self):
        self.basic_test('copy_file',
                        'Missing attribute(\'dst_url\')',
                        attributes={'src_url' :
                                        random_string()})

    def test_wrong_overwrite_value(self):
        self.basic_test('copy_file',
                        'Erroneous \'overwrite\' value',
                        attributes={'src_url' :
                                    random_string(),
                                    'dst_url' :
                                    random_string(),
                                    'overwrite' :
                                    'bogus'})

    def test_url_failure(self):
        action = get_action('copy_file')
        action = action.replace('/mnt/flash/.ztp-files',
                                '/tmp')

        self.basic_test('copy_file',
                        'Unable to retrieve file from URL',
                        attributes={'src_url' :
                                    random_string(),
                                    'dst_url' :
                                    random_string()},
                        action_value=action)


class SuccessSrcUrlReplacementTests(unittest.TestCase):

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()
        ztps_server = 'http://%s' % bootstrap.server
        url = 'http://%s/%s' % (bootstrap.server, source)

        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url'    : url,
                                      'dst_url'    : destination,
                                      'ztps_server': ztps_server}}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (destination, source)

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))
            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_append_server(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()
        ztps_server = 'http://%s' % bootstrap.server

        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                     'attributes' : {'src_url'    : source,
                                     'dst_url'    : destination,
                                     'ztps_server': ztps_server}}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (destination, source)

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))
            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()




class SuccessPersistentTest(unittest.TestCase):

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination}}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = '%s/%s' % (destination, source)

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))
            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_replace(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        attributes = {'src_url' : url,
                      'dst_url' : destination}

        # 'replace' is the default
        if bool(random.getrandbits(1)):
            attributes['overwrite'] = 'replace'

        mode = None
        if True or bool(random.getrandbits(1)):
            mode = random_permissions()
            attributes['mode'] = mode

        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : attributes}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = '%s/%s' % (destination, source)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))
            self.failIf(os.path.isfile(bootstrap.rc_eos))
            if mode:
                self.failUnless(mode ==
                                oct(os.stat(destination_path)[ST_MODE])[-3:])
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_keep_original(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination,
                                      'overwrite' : 'if-missing'}}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = '%s/%s' % (destination, source)
        existing_contents = random_string()
        os.makedirs(destination)
        file_descriptor = open(destination_path, 'w')
        file_descriptor.write(existing_contents)
        file_descriptor.close()

        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([existing_contents] ==
                            file_log(destination_path))

            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_keep_backup(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = '/tmp/%s' % random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination,
                                      'overwrite' : 'backup'}}])

        bootstrap.ztps.set_action_response(
            'startup_config_action', startup_config_action())

        action = get_action('copy_file')

        # Make the destinaton persistent
        action = action.replace('PERSISTENT_STORAGE = [',
                                'PERSISTENT_STORAGE = [\'%s\', ' %
                                destination)
        bootstrap.ztps.set_action_response('test_action',
                                           action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = '%s/%s' % (destination, source)
        backup_contents = random_string()
        os.makedirs(destination)
        file_descriptor = open(destination_path, 'w')
        file_descriptor.write(backup_contents)
        file_descriptor.close()

        bootstrap.start_test()

        backup_path = '%s.backup' % destination_path
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))

            self.failUnless(os.path.isfile(backup_path))
            self.failUnless([backup_contents] ==
                            file_log(backup_path))

            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            remove_file(backup_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

class SuccessNonPersistentTest(unittest.TestCase):

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination}}])

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

        destination_path = '%s/%s' % (persistent_dir, source)

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))

            self.failUnless(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' %
                            (destination_path, destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_replace(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        attributes = {'src_url' : url,
                      'dst_url' : destination}

        # 'replace' is the default
        if bool(random.getrandbits(1)):
            attributes['overwrite'] = 'replace'

        mode = None
        if True or bool(random.getrandbits(1)):
            mode = random_permissions()
            attributes['mode'] = mode

        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : attributes}])

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

        destination_path = '%s/%s' % (persistent_dir, source)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))

            self.failUnless(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' %
                            (destination_path, destination) in log)
            if mode:
                self.failUnless('sudo chmod %s %s' %
                                (mode, destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_original(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination,
                                      'overwrite' : 'if-missing'}}])

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

        destination_path = '%s/%s' % (persistent_dir, source)
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))

            self.failUnless(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('[ ! -f %s ] && sudo cp %s %s' %
                            (destination, destination_path,
                             destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_backup(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = 'http://%s/%s' % (bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action',
                      'attributes' : {'src_url' : url,
                                      'dst_url' : destination,
                                      'overwrite' : 'backup'}}])

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

        destination_path = '%s/%s' % (persistent_dir, source)
        try:
            self.failUnless(os.path.isfile(destination_path))
            self.failUnless([contents] ==
                            file_log(destination_path))

            self.failUnless(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.failUnless('#!/bin/bash' in log)
            self.failUnless('sudo cp %s %s' %
                            (destination_path, destination) in log)
            self.failUnless('[ -f %s ] && sudo mv %s %s.backup' %
                            (destination, destination,
                             destination) in log)
            self.failUnless(bootstrap.success())
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

if __name__ == '__main__':
    unittest.main()
