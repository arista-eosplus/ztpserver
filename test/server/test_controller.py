# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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
import json

import webob

import mock

import ztpserver.config
import ztpserver.controller
import ztpserver.neighbordb
import ztpserver.repository
from ztpserver.app import enable_handler_console

from server_test_lib import remove_all, random_string, random_json
from server_test_lib import ztp_headers, write_file

class RouterTests(unittest.TestCase):

    def match_routes(self, url, valid, invalid):

        request = webob.Request.blank(url)
        router = ztpserver.controller.Router()

        if valid:
            for method in valid.split(','):
                request.method = method
                msg = 'method %s failed for url %s' % (method, url)
                self.assertIsNotNone(router.map.match(environ=request.environ),
                                     msg)

        if invalid:
            for method in invalid.split(','):
                request.method = method
                msg = 'method %s failed for url %s' % (method, url)
                self.assertIsNone(router.map.match(environ=request.environ),
                                  msg)

    def test_bootstrap_collection(self):
        url = '/bootstrap'
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_bootstrap_resource(self):
        url = '/bootstrap/%s' % random_string()
        self.match_routes(url, None, 'GET,POST,PUT,DELETE')

    def test_files_collection(self):
        url = '/files'
        self.match_routes(url, None, 'GET,POST,PUT,DELETE')

    def test_files_resource(self):
        url = '/files/%s' % random_string()
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

        url = '/files/%s/%s' % (random_string(), random_string())
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_actions_collection(self):
        url = '/actions'
        self.match_routes(url, None, 'GET,POST,PUT,DELETE')

    def test_actions_resource(self):
        url = '/actions/%s' % random_string()
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_nodes_collection(self):
        url = '/nodes'
        self.match_routes(url, 'POST', 'GET,PUT,DELETE')

    def test_nodes_resource(self):
        url = '/nodes/%s' % random_string()
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')


class BootstrapControllerTests(unittest.TestCase):

    def setUp(self):
        self.mock_fileobj = mock.Mock(spec=ztpserver.repository.FileObject)
        self.mock_store = mock.Mock(spec=ztpserver.repository.FileStore)
        self.mock_store.get_file.return_value = self.mock_fileobj
        self.mock_store.exists.return_value = True

        ztpserver.controller.create_file_store = \
            mock.Mock(return_value=self.mock_store)

        self.router = ztpserver.controller.Router()
        self.longMessage = True

    def test_get_bootstrap(self):
        contents = random_string()

        request = webob.Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(self.router)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')

    def test_get_boostrap_config_defaults(self):

        self.mock_store.exists.return_value = False

        request = webob.Request.blank('/bootstrap/config',
                                      headers=ztp_headers())

        resp = request.get_response(self.router)

        defaultconfig = {'logging': list(), 'xmpp': dict()}

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, defaultconfig)

class FilesControllerTests(unittest.TestCase):

    def setUp(self):
        self.mock_fileobj = mock.Mock(spec=ztpserver.repository.FileObject)
        self.mock_store = mock.Mock(spec=ztpserver.repository.FileStore)
        self.mock_store.get_file.return_value = self.mock_fileobj
        self.mock_store.exists.return_value = True

        ztpserver.controller.create_file_store = \
            mock.Mock(return_value=self.mock_store)

        self.router = ztpserver.controller.Router()
        self.longMessage = True

    def tearDown(self):
        remove_all()

    def test_get_file(self):

        filename = random_string()
        filepath = write_file(random_string(), filename)

        self.mock_fileobj.name = filepath
        self.mock_fileobj.contents = filepath

        enable_handler_console()

        url = '/files/%s' % filename
        request = webob.Request.blank(url)
        resp = request.get_response(self.router)

        self.assertEqual(resp.status_code, 200)

    def test_get_missing_file(self):

        exc = mock.PropertyMock(side_effect=\
            ztpserver.repository.FileObjectNotFound)

        self.mock_store.get_file = exc

        url = '/files/%s' % random_string()

        request = webob.Request.blank(url)
        resp = request.get_response(self.router)

        self.assertEqual(resp.status_code, 404)

class ActionsControllerTests(unittest.TestCase):

    def setUp(self):
        self.mock_fileobj = mock.Mock(spec=ztpserver.repository.FileObject)
        self.mock_store = mock.Mock(spec=ztpserver.repository.FileStore)
        self.mock_store.get_file.return_value = self.mock_fileobj
        self.mock_store.exists.return_value = True

        ztpserver.controller.create_file_store = \
            mock.Mock(return_value=self.mock_store)

        self.router = ztpserver.controller.Router()
        self.longMessage = True

    def tearDown(self):
        remove_all()

    def test_get_action(self):

        filename = random_string()
        filepath = write_file(random_string(), filename)

        self.mock_fileobj.name = filename
        self.mock_fileobj.contents = filepath

        url = '/actions/%s' % filename
        request = webob.Request.blank(url)
        resp = request.get_response(self.router)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')

    def test_get_missing_action(self):

        self.mock_store.exists.return_value = False
        url = '/actions/%s' % random_string()

        request = webob.Request.blank(url)
        resp = request.get_response(self.router)

        self.assertEqual(resp.status_code, 404)

class NodesControllerTests(unittest.TestCase):

    def setUp(self):
        self.mock_fileobj = mock.Mock(spec=ztpserver.repository.FileObject)
        self.mock_store = mock.Mock(spec=ztpserver.repository.FileStore)
        self.mock_store.get_file.return_value = self.mock_fileobj
        self.mock_store.exists.return_value = True

        ztpserver.controller.create_file_store = \
            mock.Mock(return_value=self.mock_store)

        self.router = ztpserver.controller.Router()
        self.longMessage = True

if __name__ == '__main__':
    unittest.main()
