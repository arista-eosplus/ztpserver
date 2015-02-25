#!/usr/bin/env python
#
# Copyright (c) 2015 Arista Networks, Inc.
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

#pylint: disable=R0904,F0401

import os
import os.path
import unittest

from client_test_lib import Bootstrap

from client_test_lib import fail_flash_file_action
from client_test_lib import raise_exception
from client_test_lib import random_string
from client_test_lib import startup_config_action

class BootstrapCleanupTest(unittest.TestCase):

    def test_action_failure(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()

        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}])

        flash_filename = random_string()
        bootstrap.ztps.set_action_response(
                'test_action',
                fail_flash_file_action(bootstrap.flash,
                                       flash_filename))

        open(bootstrap.rc_eos, 'w').write(random_string())
        open(bootstrap.startup_config, 'w').write(random_string())
        open(bootstrap.boot_extensions, 'w').write(random_string())
        os.mkdir(bootstrap.boot_extensions_folder)
        open('%s/my_extension' % 
             bootstrap.boot_extensions_folder, 'w').write(random_string())

        bootstrap.start_test()

        try:
            self.failUnless(bootstrap.eapi_node_information_collected())
            self.failUnless(bootstrap.action_failure())
            self.failIf(bootstrap.error)
            self.failIf(os.path.isfile('%s/%s' %
                                       (bootstrap.flash,
                                        flash_filename)))
            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failIf(os.path.isfile(bootstrap.startup_config))
            self.failIf(os.path.isfile(bootstrap.boot_extensions))
            self.failIf(os.path.isdir(bootstrap.boot_extensions_folder))
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_success(self):
        bootstrap = Bootstrap()

        startup_config = random_string()

        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}])
        bootstrap.ztps.set_action_response(
            'test_action',
            startup_config_action([startup_config]))

        open(bootstrap.rc_eos, 'w').write(random_string())
        open(bootstrap.startup_config, 'w').write(startup_config + 
                                                  random_string())
        open(bootstrap.boot_extensions, 'w').write(random_string())
        os.mkdir(bootstrap.boot_extensions_folder)
        open('%s/my_extension' % 
             bootstrap.boot_extensions_folder, 'w').write(random_string())

        bootstrap.start_test()

        try:
            self.failUnless(bootstrap.eapi_node_information_collected())
            self.failUnless(bootstrap.success())
            self.failIf(bootstrap.error)

            self.failIf(os.path.isfile(bootstrap.rc_eos))
            self.failUnless(open(bootstrap.startup_config).read() ==
                           startup_config)
            self.failIf(os.path.isfile(bootstrap.boot_extensions))
            self.failIf(os.path.isdir(bootstrap.boot_extensions_folder))
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

if __name__ == '__main__':
    unittest.main()
