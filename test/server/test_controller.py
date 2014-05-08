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

#pylint: disable=C0103,E1103,W0142

import os
import unittest
import json

from webob import Request

import mock
from mock import Mock

import ztpserver.neighbordb
import ztpserver.topology
import ztpserver.controller
import ztpserver.repository
import ztpserver.config
# from ztpserver.app import enable_handler_console

from server_test_lib import remove_all, random_string
from server_test_lib import ztp_headers, write_file

class RouterTests(unittest.TestCase):

    def match_routes(self, url, valid, invalid):

        request = Request.blank(url)
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

    def test_nodes_resource_get_config(self):
        url = '/nodes/%s/startup-config' % random_string()
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')


class BootstrapControllerTests(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def test_get_bootstrap(self):

        contents = random_string()

        filestore = Mock()
        ztpserver.controller.create_file_store = filestore
        filestore.return_value.get_file.return_value = Mock(contents=contents)

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')
        self.assertEqual(resp.body, contents)

    def test_get_bootstrap_config_defaults(self):
        filestore = Mock()
        ztpserver.controller.create_file_store = filestore
        exc = Mock(side_effect=\
            ztpserver.repository.FileObjectNotFound('FileObjectNotFound'))
        filestore.return_value.get_file = exc

        request = Request.blank('/bootstrap/config')
        resp = request.get_response(ztpserver.controller.Router())

        defaultconfig = {'logging': list(), 'xmpp': dict()}

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, defaultconfig)

    def test_get_bootstrap_config(self):

        logging = [dict(destination=random_string(), level=random_string())]
        xmpp = dict(username=random_string(), domain=random_string(),
                    password=random_string(), rooms=[random_string()])
        conf = dict(logging=logging, xmpp=xmpp)
        conf = json.dumps(conf)

        filestore = Mock()
        ztpserver.controller.create_file_store = filestore
        filestore.return_value.get_file.return_value.contents = conf

        request = Request.blank('/bootstrap/config', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.body, conf)


class FilesControllerTests(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def tearDown(self):
        remove_all()

    def test_get_file(self):

        contents = random_string()
        filepath = write_file(contents)

        filestore = Mock()
        filestore.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        fileobj = Mock()
        fileobj.exists = True
        fileobj.name = filepath
        filestore.return_value.get_file = Mock(return_value=fileobj)

        filename = os.path.basename(filepath)
        url = '/files/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        filestore.return_value.get_file.assert_called_with(filename)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.body, contents)


    def test_get_missing_file(self):

        filestore = Mock()
        ztpserver.controller.create_file_store = filestore

        exc = Mock(side_effect=\
            ztpserver.repository.FileObjectNotFound('FileObjectNotFound'))
        filestore.return_value.get_file = exc

        filename = random_string()
        url = '/files/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        exc.assert_called_with(filename)
        self.assertEqual(resp.status_code, 404)

class ActionsControllerTests(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def test_get_action(self):

        contents = random_string()
        filename = random_string()

        filestore = Mock()
        filestore.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        fileobj = Mock(exists=True, name=filename, contents=contents)
        filestore.return_value.get_file = Mock(return_value=fileobj)

        url = '/actions/%s' % filename
        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        filestore.return_value.get_file.assert_called_with(filename)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')
        self.assertEqual(resp.body, contents)

    def test_get_missing_action(self):

        filestore = Mock()
        filestore.return_value.exists = Mock(return_value=False)
        ztpserver.controller.create_file_store = filestore

        filename = random_string()
        url = '/actions/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        filestore.return_value.exists.assert_called_with(filename)
        self.assertEqual(resp.status_code, 404)

class NodesControllerPostFsmTests(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def test_missing_required_attributes(self):
        url = '/nodes'
        body = json.dumps(dict())

        ztpserver.controller.create_file_store = Mock()

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())
        self.assertEqual(resp.status_code, 400)

    def test_node_exists(self):
        url = '/nodes'
        systemmac = random_string()
        body = json.dumps(dict(systemmac=systemmac))

        filestore = Mock()
        filestore.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % systemmac

        self.assertTrue(filestore.return_value.write_file.called)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.location, location)

    @mock.patch('ztpserver.neighbordb.topology')
    def test_post_config(self, _):
        url = '/nodes'
        systemmac = random_string()
        config = random_string()
        body = json.dumps(dict(systemmac=systemmac, config=config))

        filestore = Mock()
        filestore.return_value.exists.return_value = False
        ztpserver.controller.create_file_store = filestore

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % systemmac
        filename = '%s/startup-config' % systemmac

        filestore.return_value.add_folder.assert_called_with(systemmac)
        filestore.return_value.write_file.assert_called_with(filename, config)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.location, location)

    @mock.patch('ztpserver.neighbordb.topology')
    def test_post_node_success(self, _):
        url = '/nodes'
        systemmac = random_string()
        neighbors = {'Ethernet1': [{'device': 'localhost',
                                    'port': 'Ethernet1'}]}

        body = json.dumps(dict(systemmac=systemmac, neighbors=neighbors))

        filestore = Mock()
        filestore.return_value.exists.return_value = False
        filestore.return_value.get_file.return_value.contents = """
            actions:
            - name: mock definition
              action: test_action
        """
        ztpserver.controller.create_file_store = filestore

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % systemmac

        filestore.return_value.add_folder.assert_called_with(systemmac)

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.location, location)

    # @mock.patch('ztpserver.neighbordb.topology')
    # def test_post_node_definition_missing(self, *args):
    #     url = '/nodes'
    #     systemmac = random_string()
    #     neighbors = {'Ethernet1': [{'device': 'localhost',
    #                                 'port': 'Ethernet1'}]}

    #     body = json.dumps(dict(systemmac=systemmac, neighbors=neighbors))

    #     filestore = Mock()
    #     filestore.return_value.exists.return_value = False

    #     exc = Mock(side_effect=\
    #         ztpserver.repository.FileObjectNotFound('FileObjectNotFound'))
    #     filestore.return_value.get_file = exc

    #     request = Request.blank(url, body=body, method='POST',
    #                             headers=ztp_headers())
    #     resp = request.get_response(ztpserver.controller.Router())
    #     self.assertEqual(resp.status_code, 400)

    # @mock.patch('ztpserver.neighbordb.topology')
    # def test_post_node_pattern_lookup_failure(self, *args):
    #     enable_handler_console()
    #     url = '/nodes'
    #     systemmac = random_string()
    #     neighbors = {'Ethernet1': [{'device': 'localhost',
    #                                  'port': 'Ethernet1'}]}

    #     body = json.dumps(dict(systemmac=systemmac, neighbors=neighbors))

    #     filestore = Mock()
    #     filestore.return_value.exists.return_value = False
    #     filestore.return_value.get_file.return_value.contents = """
    #         actions:
    #         - name: mock definition
    #           action: test_action
    #     """
    #     ztpserver.controller.create_file_store = filestore

    #     request = Request.blank(url, body=body, method='POST',
    #                             headers=ztp_headers())
    #     resp = request.get_response(ztpserver.controller.Router())

    #     self.assertEqual(resp.status_code, 400)


class NodesControllerGetFsmTests(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def test_get_fsm_missing_node(self):
        filestore = Mock()
        filestore.return_value.exists.return_value = False
        ztpserver.controller.create_file_store = filestore

        url = '/nodes/%s' % random_string()
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)

    def test_get_startup_config_wo_validation(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        systemmac = random_string()
        filestore = Mock()

        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        fileobj = Mock()
        fileobj.contents = json.dumps(dict(systemmac=systemmac))
        filestore.return_value.get_file.return_value = fileobj

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/.node' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 200)

    def test_get_startup_config_w_validation_success(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        systemmac = random_string()
        filestore = Mock()

        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        fileobj = Mock()
        fileobj.contents = json.dumps(dict(systemmac=systemmac))
        filestore.return_value.get_file.return_value = fileobj

        ztpserver.neighbordb.load_pattern = Mock()
        cfg = {'return_value.match_node.return_value': True}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/pattern' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 200)


    def test_get_startup_config_w_validation_failure(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        systemmac = random_string()
        filestore = Mock()

        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        fileobj = Mock()
        fileobj.contents = json.dumps(dict(systemmac=systemmac))
        filestore.return_value.get_file.return_value = fileobj

        ztpserver.neighbordb.load_pattern = Mock()
        cfg = {'return_value.match_node.return_value': False}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/pattern' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)

        self.assertEqual(resp.status_code, 400)

    def test_get_definition_wo_validation(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        systemmac = random_string()

        def exists(filepath):
            if filepath.endswith('startup-config') or \
               filepath.endswith('attributes'):
                return False
            return True

        filestore = Mock()
        filestore.return_value.exists = Mock(side_effect=exists)
        ztpserver.controller.create_file_store = filestore

        attributes_file = """
            variables:
              foo: bar
        """

        definitions_file = """
            attributes:
              variables:
                foo: baz
            actions:
              - name: test action
                action: add_config
                attributes:
                  url: test
        """

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('node'):
                fileobj.contents = json.dumps(dict(systemmac=systemmac))
            elif filepath.endswith('definition'):
                fileobj.contents = definitions_file
            elif filepath.endswith('attributes'):
                fileobj.contents = attributes_file
            return fileobj

        filestore.return_value.get_file = Mock(side_effect=get_file)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/definition' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 200)

    def test_get_definition_w_validation_success(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        systemmac = random_string()

        def exists(filepath):
            if filepath.endswith('startup-config') or \
               filepath.endswith('attributes'):
                return False
            return True

        filestore = Mock()
        filestore.return_value.exists = Mock(side_effect=exists)
        ztpserver.controller.create_file_store = filestore

        attributes_file = """
            variables:
              foo: bar
        """

        definitions_file = """
            attributes:
              variables:
                foo: baz
            actions:
              - name: test action
                action: add_config
                attributes:
                  url: test
        """

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('node'):
                fileobj.contents = json.dumps(dict(systemmac=systemmac))
            elif filepath.endswith('definition'):
                fileobj.contents = definitions_file
            elif filepath.endswith('attributes'):
                fileobj.contents = attributes_file
            return fileobj

        filestore.return_value.get_file = Mock(side_effect=get_file)

        ztpserver.neighbordb.load_pattern = Mock()
        cfg = {'return_value.match_node.return_value': True}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/pattern' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 200)

    def test_get_definition_w_validation_failure(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        systemmac = random_string()

        def exists(filepath):
            if filepath.endswith('startup-config') or \
               filepath.endswith('attributes'):
                return False
            return True

        filestore = Mock()
        filestore.return_value.exists = Mock(side_effect=exists)
        ztpserver.controller.create_file_store = filestore

        attributes_file = """
            variables:
              foo: bar
        """

        definitions_file = """
            attributes:
              variables:
                foo: baz
            actions:
              - name: test action
                action: add_config
                attributes:
                  url: test
        """

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('node'):
                fileobj.contents = json.dumps(dict(systemmac=systemmac))
            elif filepath.endswith('definition'):
                fileobj.contents = definitions_file
            elif filepath.endswith('attributes'):
                fileobj.contents = attributes_file
            return fileobj

        filestore.return_value.get_file = Mock(side_effect=get_file)

        ztpserver.neighbordb.load_pattern = Mock()
        cfg = {'return_value.match_node.return_value': False}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/pattern' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 400)

    def test_get_definition_w_attributes(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        systemmac = random_string()

        def exists(filepath):
            if filepath.endswith('startup-config'):
                return False
            return True

        filestore = Mock()
        filestore.return_value.exists = Mock(side_effect=exists)
        ztpserver.controller.create_file_store = filestore

        attributes_file = """
            variables:
              foo: bar
        """

        definitions_file = """
            attributes:
              variables:
                foo: baz
            actions:
              - name: test action
                action: add_config
                attributes:
                  url: test
        """

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('node'):
                fileobj.contents = json.dumps(dict(systemmac=systemmac))
            elif filepath.endswith('definition'):
                fileobj.contents = definitions_file
            elif filepath.endswith('attributes'):
                fileobj.contents = attributes_file
            return fileobj

        filestore.return_value.get_file = Mock(side_effect=get_file)

        ztpserver.neighbordb.load_pattern = Mock()
        cfg = {'return_value.match_node.return_value': True}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        filepath = '%s/pattern' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)

        self.assertEqual(resp.status_code, 200)

        body = json.loads(resp.body)
        var_foo = body['actions'][0]['attributes']['variables']['foo']
        self.assertEqual(var_foo, 'bar')

    def test_definition_with_no_global_attributes(self):
        systemmac = random_string()

        filestore = Mock()
        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        definitions_file = """
            actions:
              - name: test action
                action: dummy_action
                attributes:
                  foo: bar
        """

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('definition'):
                fileobj.contents = definitions_file
            return fileobj

        filestore.return_value.get_file = Mock(side_effect=get_file)

        controller = ztpserver.controller.NodesController()
        resp, state = controller.get_definition(Mock(), systemmac, None)
        body = json.loads(resp.body)

        filepath = '%s/definition' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)

        self.assertTrue(state, 'get_attributes')
        self.assertTrue(resp.content_type, 'application/json')
        self.assertTrue(body['actions'][0]['attributes']['foo'], 'bar')



    def test_definition_with_global_attributes(self):
        systemmac = random_string()

        filestore = Mock()
        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        definitions_file = """
            attributes:
              foo: bar

            actions:
              - name: test action
                action: dummy_action
                attributes:
                  foo: $foo
        """

        filestore.return_value.get_file.return_value = \
            Mock(contents=definitions_file)

        controller = ztpserver.controller.NodesController()
        resp, state = controller.get_definition(Mock(), systemmac, None)
        body = json.loads(resp.body)

        filepath = '%s/definition' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)

        self.assertTrue(state, 'get_attributes')
        self.assertTrue(resp.content_type, 'application/json')
        self.assertTrue(body['actions'][0]['attributes']['foo'], 'bar')

    def test_definition_with_missing_global_attributes(self):
        systemmac = random_string()

        filestore = Mock()
        filestore.return_value.exists.return_value = True
        ztpserver.controller.create_file_store = filestore

        definitions_file = """
            attributes:
              foo: bar

            actions:
              - name: test action
                action: dummy_action
                attributes:
                  foo: $baz
        """

        filestore.return_value.get_file.return_value = \
            Mock(contents=definitions_file)

        controller = ztpserver.controller.NodesController()
        resp, state = controller.get_definition(Mock(), systemmac, None)
        body = json.loads(resp.body)

        filepath = '%s/definition' % systemmac
        filestore.return_value.get_file.assert_called_with(filepath)

        self.assertTrue(state, 'get_attributes')
        self.assertTrue(resp.content_type, 'application/json')
        self.assertIsNone(body['actions'][0]['attributes']['foo'])




if __name__ == '__main__':
    unittest.main()
