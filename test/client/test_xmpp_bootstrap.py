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

#pylint: disable=R0904,F0401

import unittest

from client_test_lib import Bootstrap
from client_test_lib import raise_exception


class XmppConfigTest(unittest.TestCase):

    @classmethod
    def bootstrap(cls, xmpp):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(xmpp=xmpp)
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()
        return bootstrap

    def xmpp_sanity_test(self, xmpp):
        bootstrap = self.bootstrap(xmpp)

        try:
            self.failUnless(bootstrap.eapi_node_information_collected())
            self.failUnless(bootstrap.missing_startup_config_failure())
            self.failIf(bootstrap.error)
            self.failIf('XmppClient' not in bootstrap.output)
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_full(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'port' : 112233,
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain',
                               'rooms' : ['test-room-1', 'test-room-2']})

    def test_msg_type_debug(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'port' : 112233,
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain',
                               'rooms' : ['test-room-1', 'test-room-2'],
                               'msg_type' : 'debug'})

    def test_msg_type_info(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'port' : 112233,
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain',
                               'rooms' : ['test-room-1', 'test-room-2'],
                               'msg_type' : 'debug'})

    def test_partial(self):
        self.xmpp_sanity_test({'rooms' : ['test-room-1'],
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain'})

    def test_erroneous_msg_type(self):
        bootstrap = self.bootstrap({'server' : 'test-server',
                                    'port' : 112233,
                                    'username' : 'test-username',
                                    'password' : 'test-password',
                                    'domain' :   'test-domain',
                                    'rooms' : ['test-room-1', 'test-room-2'],
                                    'msg_type' : 'bogus'})

        try:
            self.failUnless(bootstrap.eapi_node_information_collected())
            self.failUnless(bootstrap.missing_startup_config_failure())
            self.failIf(bootstrap.error)
            self.failIf('XMPP configuration failed because of '
                        'unexpected \'msg_type\''
                        not in bootstrap.output)
        except AssertionError as assertion:
            print 'Output: %s' % bootstrap.output
            print 'Error: %s' % bootstrap.error
            raise_exception(assertion)
        finally:
            bootstrap.end_test()



if __name__ == '__main__':
    unittest.main()
