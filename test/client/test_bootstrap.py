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

#pylint: disable=R0904

import os
import os.path
import unittest

from client_test_lib import debug    #pylint: disable=W0611
from client_test_lib import Bootstrap, BaseTest
from client_test_lib import cli_log, file_log, remove_file
from client_test_lib import startup_config_action, clear_startup_config
from client_test_lib import fail_action, print_action, random_string


class ServerNotRunningTest(BaseTest):
    
    def test(self):
        bootstrap = Bootstrap(server='127.0.0.2')
        bootstrap.start_test()

        self.failUnless(bootstrap.server_connection_failure())
        self.assertEquals(cli_log(), [])
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class ConfigRequestErrorTest(BaseTest):

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(status=201)
        bootstrap.start_test()

        self.failUnless(bootstrap.unexpected_response_failure())
        self.assertEquals(cli_log(), [])
        self.failIf(bootstrap.error)
        bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.unexpected_response_failure())
        self.assertEquals(cli_log(), [])
        self.failIf(bootstrap.error)
        bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(
            status=201,
            content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.unexpected_response_failure())
        self.assertEquals(cli_log(), [])
        self.failIf(bootstrap.error)
        bootstrap.end_test()


class EAPIErrorTest(BaseTest):

    def test(self):
        bootstrap = Bootstrap(eapi_port=54321)
        bootstrap.ztps.set_config_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_configured())
        self.failUnless(bootstrap.eapi_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class CheckNodeErrorTest(BaseTest):

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(status=200)
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(
            content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(
            status=200,
            content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_node_not_found(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(status=400)
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.node_not_found_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class DefinitionErrorTest(BaseTest):

    def test_definition_missing(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.server_connection_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(status=201)

        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            status=201,
            content_type='text/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

    def test_topology_check(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            status=400,
            content_type='text/html')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.toplogy_check_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class MissingStartupConfigTest(BaseTest):

    def test(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class FileLogConfigTest(BaseTest):

    def test(self):
        filenames = {
            'DEBUG' : '/tmp/ztps-log-%s-debug' % os.getpid(),
            'ERROR' : '/tmp/ztps-log-%s-error' % os.getpid(),
            'INFO' : '/tmp/ztps-log-%s-info' % os.getpid(),
            'bogus' : '/tmp/ztps-log-%s-bogus' % os.getpid() 
            }

        logging = []
        for level, filename in filenames.iteritems():
            logging += {'destination' : 'file:%s' % filename,
                        'level' : level},

        for filename in filenames.itervalues():
            self.failIf(os.path.isfile(filename))

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=logging)
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        for filename in filenames.itervalues():
            self.failUnless(file_log(filename))
        self.assertEquals(file_log(filenames['DEBUG']),
                         file_log(filenames['bogus']))
        self.assertEquals(file_log(filenames['DEBUG']),
                         file_log(filenames['INFO']))
        self.failIfEqual(file_log(filenames['DEBUG']),
                            file_log(filenames['ERROR']))
        self.failUnless(set(file_log(filenames['ERROR'])).issubset(
                set(file_log(filenames['DEBUG']))))
        for filename in filenames.itervalues():
            remove_file(filename)
        self.failIf(bootstrap.error)

        bootstrap.end_test()


class XmppConfigTest(BaseTest):

    def test_full(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'port' : 112233,
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain',
                               'nickname' : 'test-nickname',
                               'rooms' : ['test-room-1', 'test-room-2']})


    def test_partial(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain'})

    def xmpp_sanity_test(self, xmpp):
        log = '/tmp/ztps-log-%s-debug' % os.getpid()

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=[
                {'destination' : 'file:%s' % log,
                 'level' : 'DEBUG'},],
                                           xmpp=xmpp)
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        self.failIf(bootstrap.error)
        self.failIf('XmppClient' not in ''.join(file_log(log)))

        bootstrap.end_test()


class ActionFailureTest(BaseTest):

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'test_action' : {}})
        bootstrap.ztps.set_action_response('test_action', print_action(),
                                           status=201)
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'test_action' : {}})
        bootstrap.ztps.set_action_response('test_action', print_action(),
                                           content_type='test/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'test_action' : {}})
        bootstrap.ztps.set_action_response('test_action', print_action(),
                                           status=201,
                                           content_type='test/plain')
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.unexpected_response_failure())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    def test_action_failed(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'test_action' : {}})
        bootstrap.ztps.set_action_response('test_action', fail_action())
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.action_failure())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    def test_action_failure_log(self):
        log = '/tmp/ztps-log-%s-debug' % os.getpid()

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=[
                {'destination' : 'file:%s' % log,
                 'level' : 'DEBUG'},])
        bootstrap.ztps.set_node_check_response()

        text_onstart = random_string()
        text_onsuccess = random_string()
        text_onfailure = random_string()
        bootstrap.ztps.set_definition_response(
            actions={'test_action' : {'onstart' : text_onstart,
                                      'onsuccess' : text_onsuccess,
                                      'onfailure' : text_onfailure},
                     })
        bootstrap.ztps.set_action_response('test_action',
                                           fail_action())
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.action_failure())
        self.failIf(bootstrap.error)
        log  = ''.join(file_log(log))
        self.failUnless(text_onstart in log)
        self.failUnless(text_onsuccess not in log)
        self.failUnless(text_onfailure in log)

        clear_startup_config()
        bootstrap.end_test()


class BootstrapSuccessTest(BaseTest):

    def test_success(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'save_config' : {}})
        bootstrap.ztps.set_action_response('save_config',
                                           startup_config_action())
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.success())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    def test_multiple_actions(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions={'save_config' : {},
                                                        'print_action_1' : {},
                                                        'print_action_2' : {}})
        bootstrap.ztps.set_action_response('save_config',
                                           startup_config_action())

        text_1 = random_string()
        bootstrap.ztps.set_action_response('print_action_1',
                                           print_action(text_1))
        text_2 = random_string()
        bootstrap.ztps.set_action_response('print_action_2',
                                           print_action(text_2))
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.success())
        self.failUnless(text_1 in bootstrap.output)
        self.failUnless(text_2 in bootstrap.output)
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

    # Not supported yet
    # def test_attributes(self):
    #     bootstrap = Bootstrap()
    #     bootstrap.ztps.set_config_response()
    #     bootstrap.ztps.set_node_check_response()
    #     text = random_string()
    #     bootstrap.ztps.set_definition_response(
    #         actions={'save_config' : {},
    #                  'print_action' : {}},
    #         attributes={'print_action':text})
    #     bootstrap.ztps.set_action_response('save_config',
    #                                    startup_config_action())
    #     bootstrap.ztps.set_action_response('print_action',
    #                                        print_action(use_attribute=True))
    #     bootstrap.start_test()

    #     self.failUnless(bootstrap.eapi_node_information_collected())
    #     self.failUnless(bootstrap.success())
    #     debug()

    #     self.failUnless(text in bootstrap.output)

    #     self.failIf(bootstrap.error)

    #     clear_startup_config()
    #     bootstrap.end_test()

    def test_action_success_log(self):
        log = '/tmp/ztps-log-%s-debug' % os.getpid()

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=[
                {'destination' : 'file:%s' % log,
                 'level' : 'DEBUG'},])
        bootstrap.ztps.set_node_check_response()

        text_onstart = random_string()
        text_onsuccess = random_string()
        text_onfailure = random_string()
        bootstrap.ztps.set_definition_response(
            actions={'save_config' : {'onstart' : text_onstart,
                                      'onsuccess' : text_onsuccess,
                                      'onfailure' : text_onfailure},
                     })
        bootstrap.ztps.set_action_response('save_config',
                                           startup_config_action())
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.success())
        self.failIf(bootstrap.error)
        log  = ''.join(file_log(log))
        self.failUnless(text_onstart in log)
        self.failUnless(text_onsuccess in log)
        self.failUnless(text_onfailure not in log)

        clear_startup_config()
        bootstrap.end_test()


if __name__ == '__main__':
    unittest.main()
