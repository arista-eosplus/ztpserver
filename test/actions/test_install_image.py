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
import unittest
import sys

sys.path.append('test/client')

from client_test_lib import debug    #pylint: disable=W0611
from client_test_lib import FLASH, STARTUP_CONFIG
from client_test_lib import Bootstrap, ActionFailureTest
from client_test_lib import file_log, remove_file, get_action
from client_test_lib import startup_config_action, random_string
from client_test_lib import print_action

class FailureTest(ActionFailureTest):

    def test_missing_url(self):
        self.basic_test('install_image', 1)

    def test_missing_software_version(self):
        self.basic_test('install_image', 2,
                        attributes={'software_url' :
                                        random_string()})

    def test_url_failure(self):
        self.basic_test('install_image', 3,
                        attributes={'software_url' :
                                    random_string(),
                                    'software_version' :
                                    random_string()})


class SuccessTest(unittest.TestCase):

    def test_no_op(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version = random_string()
        bootstrap.eapi.version = version
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'},
                     {'action' :'startup_config_action'}],
            attributes={
                'software_url' : random_string(),
                'software_version' : version})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('install_image'))
        bootstrap.ztps.set_action_response('startup_config_action',
                                           startup_config_action())
        bootstrap.start_test()

        try:
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version = random_string()
        image = random_string()
        url = 'http://%s/%s' % (bootstrap.server, image)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={
                'software_url' : url,
                'software_version' : version})

        boot_file = '/tmp/boot-config'
        action = get_action('install_image')
        action = action.replace('/mnt/flash/boot-config',
                                boot_file)
        bootstrap.ztps.set_action_response('test_action',
                                           action)
        bootstrap.ztps.set_file_response(image, print_action())
        bootstrap.start_test()

        image_file = '%s/%s.swi' % (FLASH, version)
        try:
            self.failUnless('! boot system flash:/%s.swi' % version
                            in file_log(STARTUP_CONFIG))
            self.failUnless(os.path.isfile(image_file))
            self.failUnless(['SWI=flash:/%s.swi' % version] ==
                            file_log(boot_file))
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(image_file)
            remove_file(boot_file)
            bootstrap.end_test()

    def test_startup_config(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version = random_string()
        image = random_string()
        url = 'http://%s/%s' % (bootstrap.server, image)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action'}],
            attributes={
                'software_url' : url,
                'software_version' : version})
        wrong_version = '%s_test' % version
        bootstrap.ztps.set_action_response(
            'startup_config_action',
            startup_config_action(lines=['! boot system flash:/%s.swi' %
                                         wrong_version]))

        boot_file = '/tmp/boot-config'
        action = get_action('install_image')
        action = action.replace('/mnt/flash/boot-config',
                                boot_file)
        bootstrap.ztps.set_action_response('test_action',
                                           action)
        bootstrap.ztps.set_file_response(image, print_action())
        bootstrap.start_test()

        image_file = '%s/%s.swi' % (FLASH, version)
        try:
            self.failUnless('! boot system flash:/%s.swi' % version
                            in file_log(STARTUP_CONFIG))
            self.failUnless('! boot system flash:/%s.swi' % wrong_version
                            not in file_log(STARTUP_CONFIG))
            self.failUnless(os.path.isfile(image_file))
            self.failUnless(['SWI=flash:/%s.swi' % version] ==
                            file_log(boot_file))
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            remove_file(image_file)
            remove_file(boot_file)
            bootstrap.end_test()


if __name__ == '__main__':
    unittest.main()
