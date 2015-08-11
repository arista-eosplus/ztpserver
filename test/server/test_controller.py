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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0102,C0103,E1103,W0142,W0613,C0302,E1120
#

import json
import random
import unittest

from webob import Request

from mock import MagicMock, Mock, patch

import ztpserver.controller
import ztpserver.config
import ztpserver.repository

from ztpserver.controller import DEFINITION_FN, PATTERN_FN

from ztpserver.repository import FileObjectNotFound, FileObjectError

from server_test_lib import enable_logging, remove_all, random_string
from server_test_lib import mock_match, ztp_headers, write_file
from server_test_lib import create_definition, create_attributes, create_node
from server_test_lib import create_bootstrap_conf

import ztpserver.constants as constants


class RouterUnitTests(unittest.TestCase):

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

    def test_bootstrap_config(self):
        url = '/bootstrap/config'
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_meta_action(self):
        url = '/meta/actions/dummy'
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_meta_files(self):
        url = '/meta/files/dummy'
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

    def test_meta_files_long(self):
        url = '/meta/files/dummy/long'
        self.match_routes(url, 'GET', 'POST,PUT,DELETE')

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
        self.match_routes(url, 'GET,PUT', 'POST,DELETE')



class MetaControllerUnitTests(unittest.TestCase):

    @patch('ztpserver.controller.create_repository')
    def test_bad_request_file_not_found(self, m_repository):
        error = IOError
        cfg = {'return_value.get_file.side_effect': error}
        m_repository.configure_mock(**cfg)

        path = '/'.join([random_string()] * random.randint(1, 4))

        controller = ztpserver.controller.MetaController()
        resp = controller.metadata(None,
                                   type=random.choice(['files', 'actions']),
                                   path_info=path)

        self.assertEqual(resp['body'], '')
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_HTML)
        self.assertEqual(resp['status'], constants.HTTP_STATUS_NOT_FOUND)

    @patch('ztpserver.controller.create_repository')
    def test_bad_request_io_error(self, m_repository):
        cfg = random.choice([
                {'return_value.get_file.return_value.hash.side_effect':
                 IOError},
                {'return_value.get_file.return_value.size.side_effect':
                 IOError}])
        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.MetaController()
        resp = controller.metadata(None,
                                   type=random.choice(['files', 'actions']),
                                   path_info=random_string())

        self.assertEqual(resp['body'], '')
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_HTML)
        self.assertEqual(resp['status'],
                         constants.HTTP_STATUS_INTERNAL_SERVER_ERROR)

    @patch('ztpserver.controller.create_repository')
    def test_success(self, m_repository):
        sha1 = random_string()
        size = random.randint(1, 1000000)
        cfg = {'return_value.get_file.return_value.hash.return_value':
               sha1,
               'return_value.get_file.return_value.size.return_value':
               size}
        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.MetaController()
        resp = controller.metadata(None,
                                   type=random.choice(['files', 'actions']),
                                   path_info=random_string())

        self.assertEqual(resp['body'], {'sha1': sha1, 'size': size})
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)


class BootstrapConfigUnitTests(unittest.TestCase):

    @patch('ztpserver.controller.create_repository')
    @patch('string.Template.safe_substitute')
    def test_index_success(self, m_substitute, m_repository):
        m_substitute.return_value = random_string()

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.index(request)

        self.assertTrue(m_substitute.called)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_PYTHON)
        self.assertEqual(resp['body'], m_substitute.return_value)

    @patch('ztpserver.controller.create_repository')
    def test_index_bootstrap_not_found_failure(self, m_repository):
        cfg = {'return_value.get_file.side_effect': FileObjectError}
        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.index(None)

        self.assertTrue(resp['status'], constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp['body'], '')

    @patch('ztpserver.controller.create_repository')
    def test_index_bootstrap_inaccessible_failure(self, m_repository):
        cfg = {'return_value.read.side_effect': FileObjectError}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.index(None)

        self.assertTrue(resp['status'], constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp['body'], '')

    @patch('ztpserver.controller.create_repository')
    def test_config_success(self, m_repository):
        config = create_bootstrap_conf()
        config.add_logging(dict(destination=random_string(),
                                level=random_string()))

        cfg = {'return_value.read.return_value': config.as_dict()}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], config.as_dict())
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_config_defaults(self, m_repository):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_config_failure(self, m_repository):
        cfg = {'return_value.read.side_effect': FileObjectError}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.config(None)

        self.assertEqual(resp['body'], '')
        self.assertEqual(resp['status'], constants.HTTP_STATUS_BAD_REQUEST)

    @patch('ztpserver.controller.create_repository')
    def test_no_config(self, m_repository):
        cfg = {'return_value.read.return_value': {}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_no_xmpp(self, m_repository):
        cfg = {'return_value.read.return_value': {'logging': []}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_no_logging(self, m_repository):
        cfg = {'return_value.read.return_value': {'xmpp': {}}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)


    @patch('ztpserver.controller.create_repository')
    def test_empty_xmpp(self, m_repository):
        cfg = {'return_value.read.return_value': {'logging': [],
                                                  'xmpp': None}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_empty_logging(self, m_repository):
        cfg = {'return_value.read.return_value': {'logging': None,
                                                  'xmpp': {}}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)

    @patch('ztpserver.controller.create_repository')
    def test_empty_xmpp_logging(self, m_repository):
        cfg = {'return_value.read.return_value': {'logging': None,
                                                  'xmpp': None}}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()

        request = Request.blank('')
        request.remote_addr = ''
        resp = controller.config(request)

        self.assertEqual(resp['body'], controller.DEFAULT_CONFIG)
        self.assertEqual(resp['content_type'], constants.CONTENT_TYPE_JSON)


class BootstrapUnitTests(unittest.TestCase):

    def setUp(self):
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    @patch('string.Template.safe_substitute')
    def test_get_bootstrap_success(self, m_substitute):
        contents = random_string()
        m_substitute.return_value = contents

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_PYTHON)
        self.assertEqual(resp.body, contents)

    def test_get_bootstrap_missing(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_HTML)

    @patch('string.Template.safe_substitute')
    def test_get_bootstrap_misconfigured(self, m_substitute):
        m_substitute.side_effect = KeyError

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_HTML)

    def test_get_bootstrap_inaccessible(self):
        cfg = {'return_value.get_file.side_effect': FileObjectError}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_HTML)

    def test_get_bootstrap_config_success(self):
        config = create_bootstrap_conf()
        config.add_logging(dict(destination=random_string(),
                                level=random_string()))

        cfg = {'return_value.read.return_value': config.as_dict()}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        request = Request.blank('/bootstrap/config')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertEqual(json.loads(resp.body), config.as_dict())

    def test_get_bootstrap_config_defaults(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap/config')
        resp = request.get_response(ztpserver.controller.Router())

        defaultconfig = {'logging': list(), 'xmpp': dict()}

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertEqual(json.loads(resp.body), defaultconfig)


class FilesControllerIntegrationTests(unittest.TestCase):

    def tearDown(self):
        remove_all()

    @patch('ztpserver.controller.create_repository')
    def test_get_file_success(self, m_repository):
        contents = random_string()
        filepath = write_file(contents)

        m_repository.return_value.get_file.return_value.name = filepath

        url = '/files/%s' % filepath
        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        m_repository.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_OTHER)
        self.assertEqual(resp.body, contents)


    @patch('ztpserver.controller.create_repository')
    def test_get_missing_file(self, m_repository):
        cfg = {'return_value.get_file.side_effect':
                    ztpserver.repository.FileObjectNotFound}
        m_repository.configure_mock(**cfg)

        filename = random_string()
        url = '/files/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        filepath = 'files/%s' % filename
        m_repository.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_NOT_FOUND)


class ActionsControllerIntegrationTests(unittest.TestCase):

    @patch('ztpserver.controller.create_repository')
    def test_get_action_success(self, m_repository):
        contents = random_string()
        cfg = {'return_value.read.return_value': contents}
        m_repository.return_value.get_file.configure_mock(**cfg)

        filename = random_string()
        url = '/actions/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        m_repository.return_value.get_file.assert_called_with(url[1:])
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_PYTHON)
        self.assertEqual(resp.body, contents)

    @patch('ztpserver.controller.create_repository')
    def test_get_action_missing(self, m_repository):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        m_repository.configure_mock(**cfg)

        filename = random_string()
        url = '/actions/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_NOT_FOUND)


class NodesControllerUnitTests(unittest.TestCase):


    def tearDown(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')
        ztpserver.config.runtime.set_value(\
            'identifier', 'serialnumber', 'default')
        
    @classmethod
    def identifier(cls, node):
        identifier = ztpserver.config.runtime.default.identifier
        if identifier == 'systemmac':
            return node.systemmac
        else:
            return node.serialnumber

    @patch('ztpserver.controller.create_repository')
    def test_create(self, m_repository):
        node = Mock(systemmac=random_string(), serialnumber=random_string())
        body = dict(systemmac=node.systemmac, serialnumber=node.serialnumber)

        request = Request.blank('/nodes')
        request.body = json.dumps(body)

        controller = ztpserver.controller.NodesController()
        with patch.object(controller, 'fsm') as m_fsm:
            controller.create(request)
            self.assertEqual(self.identifier(node),
                             m_fsm.call_args[1]['node_id'])

    @patch('ztpserver.controller.create_repository')
    def test_create_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_create()

    @patch('ztpserver.controller.create_repository')
    def test_create_missing_identifier(self, m_repository):
        node = Mock(systemmac=None, serialnumber=None)
        body = dict(systemmac=node.systemmac, serialnumber=node.serialnumber)

        request = Request.blank('/nodes')
        request.body = json.dumps(body)

        controller = ztpserver.controller.NodesController()
        resp = controller.create(request)
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)

    @patch('ztpserver.controller.create_repository')
    def test_create_missing_identifier_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_create_missing_identifier()

    @patch('ztpserver.controller.create_repository')
    def test_node_exists(self, m_repository):
        m_repository.return_value.exists.return_value = True

        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'dump_node')
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CONFLICT)

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_node_exists()


    @patch('ztpserver.controller.create_repository')
    def test_node_exists_definition_exists(self, m_repository):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(DEFINITION_FN):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'dump_node')
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CONFLICT)

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_definition_exists_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_node_exists_definition_exists()

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_startup_config_exists(self, m_repository):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(ztpserver.controller.STARTUP_CONFIG_FN):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'dump_node')
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CONFLICT)

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_startup_config_exists_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_node_exists_startup_config_exists()

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_sysmac_folder_exists(self, m_repository):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(self.identifier(node)):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, None)
        self.assertEqual(resp['status'],
                         constants.HTTP_STATUS_BAD_REQUEST)

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_sysmac_folder_exists_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_node_exists_sysmac_folder_exists()

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_failure(self, m_repository):
        m_repository.return_value.exists.return_value = False

        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())
        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'post_config')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    @patch('ztpserver.controller.create_repository')
    def test_node_exists_failure_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_node_exists_failure()

    @patch('ztpserver.controller.create_repository')
    def test_dump_node_success(self, m_repository):
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        cfg = dict()
        cfg['return_value.get_file'] = Mock()
        m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.dump_node(dict(), node=node,
                                             node_id=self.identifier(node))

        self.assertEqual(state, 'set_location')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    @patch('ztpserver.controller.create_repository')
    def test_dump_node_success_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_dump_node_success()

    @patch('ztpserver.controller.create_repository')
    def test_dump_node_write_file_failure(self, m_repository):

        cfg = {'return_value.get_file.return_value.write.side_effect': \
               ztpserver.repository.FileObjectError}
        m_repository.configure_mock(**cfg)

        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        self.assertRaises(ztpserver.repository.FileObjectError,
                          controller.dump_node,
                          dict(),
                          node=node,
                          node_id=self.identifier(node))

    @patch('ztpserver.controller.create_repository')
    def test_dump_node_write_file_failure_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_dump_node_write_file_failure()

    def test_set_location_success(self):
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())
        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.set_location(dict(), node=node,
                                                node_id=self.identifier(node))

        location = 'nodes/%s' % self.identifier(node)
        self.assertIsNone(state)
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['location'], location)

    def test_set_location_failure(self):
        controller = ztpserver.controller.NodesController()
        self.assertRaises(AttributeError, controller.set_location,
                          dict(), node=None)

    def test_post_config_success(self):
        request = Mock(json=dict(config=random_string()))
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_config(dict(), request=request,
                                               node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'set_location')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CREATED)

    def test_post_config_success_systemmac(self):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_config_success()

    def test_post_config_key_error_failure(self):
        request = Mock(json=dict())
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_config(dict(), request=request,
                                               node=node,
                                               node_id=self.identifier(node))

        self.assertEqual(state, 'post_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    def test_post_config_key_error_failure_systemmac(self):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_config_key_error_failure()

    def test_post_config_failure(self):
        controller = ztpserver.controller.NodesController()
        self.assertRaises(Exception, controller.post_config, dict())

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_success_single_match(self, m_load_neighbordb):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        m_load_neighbordb.return_value.match_node.return_value = [mock_match()]
        controller = ztpserver.controller.NodesController()

        (resp, state) = controller.post_node(dict(), request=request, node=node,
                                             node_id=self.identifier(node))

        self.assertEqual(state, 'dump_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CREATED)

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_success_single_match_systemmac(self, m_load_neighbordb):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_node_success_single_match()

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_success_multiple_matches(self, m_load_neighbordb):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        m_load_neighbordb.return_value.match_node.return_value = [mock_match(),
                                                                  mock_match(),
                                                                  mock_match()]

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_node(dict(), request=request, node=node,
                                             node_id=self.identifier(node))

        self.assertEqual(state, 'dump_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], constants.HTTP_STATUS_CREATED)

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_success_multiple_matches_systemmac(self,
                                                          m_load_neighbordb):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_node_success_multiple_matches()

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_failure_no_matches(self, m_load_neighbordb):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        m_load_neighbordb.return_value.match_node.return_value = list()

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_node(dict(), request=request,
                                             node=node,
                                             node_id=self.identifier(node))
        self.assertEqual(state, None)
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], constants.HTTP_STATUS_BAD_REQUEST)

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_failure_no_matches_systemac(self, m_load_neighbordb):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_node_failure_no_matches()

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_no_definition_in_pattern(self, m_load_neighbordb):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(serialnumber=random_string(),
                    systemmac=random_string())

        pattern = Mock()
        del pattern.definition

        m_load_neighbordb.return_value.match_node.return_value = [pattern]

        controller = ztpserver.controller.NodesController()
        self.assertRaises(AttributeError, controller.post_node, dict(),
                          request=request, node=node,
                          node_id=self.identifier(node))

    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_no_definition_in_pattern_systemmac(self,
                                                          m_load_neighbordb):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_post_node_no_definition_in_pattern()

    @patch('ztpserver.controller.create_repository')
    def test_get_definition_success(self, m_repository):
        cfg = {'return_value.read.return_value': MagicMock()}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_definition(dict(),
                                                  resource=random_string())

        self.assertEqual(state, 'get_attributes')
        self.assertIsInstance(resp, dict)

    @patch('ztpserver.controller.replace_config_action')
    def test_get_startup_config_success(self, m_replace_config_action):
        m_replace_config_action.return_value = dict()

        ztpserver.topology.replace_config_action = Mock(return_value=dict())

        response = dict(definition={'actions': list()})

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_startup_config(response,
                                                      resource=random_string())

        self.assertEqual(state, 'get_definition')
        self.assertIsInstance(resp, dict)


    @patch('ztpserver.controller.replace_config_action')
    def test_get_startup_config_success_no_definition(self,
                                                      m_replace_config_action):
        resource = random_string()

        action_name = random_string()
        action = {'name': action_name, 'action': 'replace_config'}
        m_replace_config_action.return_value = action
        ztpserver.topology.replace_config_action = Mock(return_value=action)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_startup_config(dict(), resource=resource)

        self.assertEqual(state, 'get_definition')
        self.assertIsInstance(resp, dict)
        self.assertTrue(resp['get_startup_config'])
        self.assertTrue(resp['definition'], 'Autogenerated definition')
        self.assertEqual(resp['definition']['actions'][0]['name'], action_name)

    @patch('ztpserver.controller.load_pattern')
    def test_do_validation_success(self, m_load_pattern):

        cfg = {'return_value.match_node.return_value': True}
        m_load_pattern.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_validation(dict(),
                                                 resource=random_string(),
                                                 node=Mock())

        self.assertEqual(state, 'get_startup_config')
        self.assertIsInstance(resp, dict)

    def test_do_validation_disabled_success(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_validation(dict(),
                                                 resource=random_string())

        self.assertEqual(state, 'get_startup_config')
        self.assertIsInstance(resp, dict)

    @patch('ztpserver.controller.create_repository')
    def test_get_attributes_success(self, m_repository):
        cfg = {'return_value.read.return_value': random_string()}
        m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_attributes(dict(),
                                                  resource=random_string())

        self.assertEqual(state, 'do_substitution')
        self.assertIsInstance(resp, dict)

    @patch('ztpserver.controller.create_repository')
    def test_get_attributes_missing(self, m_repository):
        node = create_node()

        m_repository.return_value.exists.return_value = False
        m_repository.return_value.get_file = \
            Mock(side_effect=ztpserver.repository.FileObjectNotFound)


        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_attributes(
            dict(),
            resource=self.identifier(node))

        self.assertEqual(state, 'do_substitution')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['attributes'], dict())

    @patch('ztpserver.controller.create_repository')
    def test_get_attributes_missing_systemmac(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'identifier', 'systemmac', 'default')
        self.test_get_attributes_missing()

    def test_do_substitution_success(self):
        defattrs = dict(foo='$foo')

        definition = create_definition()
        definition.add_attribute('foo', 'bar')
        definition.add_action(name='dummy action', attributes=defattrs)

        response = dict(definition=definition.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_substitution(response,
                                                   resource=random_string())

        self.assertEqual(state, 'do_resources')
        self.assertIsInstance(resp, dict)

        foo = resp['definition']['actions'][0]['attributes']['foo']
        self.assertEqual(foo, 'bar')

    def test_do_substitution_with_attributes(self):
        defattrs = dict(foo='$foo')

        definition = create_definition()
        definition.add_attribute('foo', 'bar')
        definition.add_action(name='dummy action', attributes=defattrs)

        g_attr_foo = random_string()
        attributes = create_attributes()
        attributes.add_attribute('foo', g_attr_foo)

        response = dict(definition=definition.as_dict(),
                        attributes=attributes.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_substitution(response,
                                                   resource=random_string())

        self.assertEqual(state, 'do_resources')
        self.assertIsInstance(resp, dict)

        foo = resp['definition']['actions'][0]['attributes']['foo']
        self.assertEqual(foo, g_attr_foo)

    def test_do_substitution_without_actions(self):
        # github issue #129
        definition = create_definition()
        definition.actions.append({'name': 'foo'})
        response = dict(definition=definition.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_substitution(response,
                                                   resource=random_string())

        self.assertEqual(state, 'do_resources')
        self.assertIsInstance(resp, dict)

    def test_do_resources_success(self):
        var_foo = random_string()
        ztpserver.controller.load_resources = \
            Mock(return_value=dict(foo=var_foo))

        definition = create_definition()
        definition.add_action(name='dummy action',
                              attributes=dict(foo=random_string()))

        response = dict(definition=definition.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_resources(response, node=Mock(),
                                                resource=random_string())

        self.assertEqual(state, 'finalize_response')
        self.assertIsInstance(resp, dict)
        foo = resp['definition']['actions'][0]['attributes']['foo']
        self.assertEqual(foo, var_foo)

    @patch('os.path.isfile')
    def test_put_config_success(self, m_is_file):
        m_is_file.return_value = False

        resource = random_string()
        body = random_string()
        request = Mock(content_type=constants.CONTENT_TYPE_OTHER, body=body)

        controller = ztpserver.controller.NodesController()
        resp = controller.put_config(request,
                                     resource=resource)

        self.assertEqual(resp, dict())


class NodesControllerPostFsmIntegrationTests(unittest.TestCase):

    def setUp(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

    @patch('ztpserver.controller.create_repository')
    def test_missing_required_attributes(self, m_repository):
        url = '/nodes'
        body = json.dumps(dict())

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())

        resp = request.get_response(ztpserver.controller.Router())
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)

    @patch('ztpserver.controller.create_repository')
    def test_node_exists(self, m_repository):
        url = '/nodes'
        serialnumber = random_string()
        body = json.dumps(dict(serialnumber=serialnumber))

        m_repository.return_value.exists.return_value = True

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())

        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % serialnumber
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_CONFLICT)
        self.assertEqual(resp.location, location)

    @patch('ztpserver.controller.create_repository')
    def test_post_config(self, m_repository):
        url = '/nodes'
        serialnumber = random_string()
        config = random_string()
        body = json.dumps(dict(serialnumber=serialnumber, config=config))

        m_repository.return_value.exists.return_value = False

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % serialnumber
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_CREATED)
        self.assertEqual(resp.location, location)

    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_neighbordb')
    def test_post_node_success(self, m_load_neighbordb, m_repository):
        node = create_node()

        definition = create_definition()
        definition.add_action()

        cfg = {'return_value.exists.return_value': False}
        m_repository.configure_mock(**cfg)

        pattern_name = random_string()
        cfg = {'return_value.match_node.return_value':
               [mock_match(name=pattern_name)]}
        m_load_neighbordb.configure_mock(**cfg)

        request = Request.blank('/nodes', body=node.as_json(), method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        args_list = list()
        args_list.append('nodes/%s/%s' % (node.serialnumber, DEFINITION_FN))
        args_list.append('nodes/%s/%s' % (node.serialnumber, PATTERN_FN))

        for arg in args_list:
            m_repository.return_value.add_file.assert_any_call(arg)

        write_mock = m_repository.return_value.add_file.return_value.write
        # 'definition' is not written to the pattern file
        # Empty 'variables', 'node' are not written to the
        # pattern file either
        self.assertEqual(sorted(write_mock.call_args_list[1][0][0].keys()),
                         ['interfaces', 'name'])

        location = 'http://localhost/nodes/%s' % node.serialnumber
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_CREATED)
        self.assertEqual(resp.location, location)


class NodesControllerGetFsmIntegrationTests(unittest.TestCase):

    def setUp(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

    @patch('ztpserver.controller.create_repository')
    def test_get_fsm_missing_node(self, m_repository):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % random_string()
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)


    @patch('ztpserver.controller.create_node')
    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_startup_config_wo_validation(self, m_load_pattern,
                                              m_repository, m_create_node):

        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        definition = create_definition()
        definition.add_action()

        node = create_node()
        cfg = dict()

        def m_get_file(arg):
            fileobj = Mock()
            if arg.endswith('.node'):
                fileobj.return_value.read.return_value = node.as_dict()
            elif arg.endswith('startup-config'):
                fileobj.return_value.read.return_value = random_string()
            else:
                raise ztpserver.repository.FileObjectNotFound
            return fileobj
        cfg['return_value.get_file'] = Mock(side_effect=m_get_file)

        m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertIsInstance(json.loads(resp.body), dict)

    @patch('ztpserver.controller.load_pattern')
    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.create_node')
    def test_get_startup_config_w_validation_success(self,
                                                     m_load_pattern,
                                                     m_repository,
                                                     m_create_node):

        definition = create_definition()
        definition.add_action()

        node = create_node()
        cfg = dict()

        def m_get_file(arg):
            fileobj = Mock()
            if arg.endswith('.node'):
                fileobj.read.return_value = node.as_dict()
            elif arg.endswith('startup-config'):
                fileobj.read.return_value = random_string()
            elif arg.endswith('pattern'):
                fileobj.read.return_value = random_string()
            else:
                raise ztpserver.repository.FileObjectNotFound
            return fileobj

        cfg['return_value.get_file'] = Mock(side_effect=m_get_file)

        m_repository.configure_mock(**cfg)

        cfg = {'return_value.match_node.return_value': True}
        m_load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertIsInstance(json.loads(resp.body), dict)

    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_startup_config_w_validation_failure(self, m_load_pattern,
                                                     m_repository):

        m_load_pattern.return_value.match_node.return_value = list()

        node = create_node()
        cfg = dict()

        def exists(filepath):
            if filepath.endswith('startup-config'):
                return True
            return False
        cfg['return_value.exists'] = Mock(side_effect=exists)

        def get_file(filepath):
            fileobj = Mock()
            if filepath.endswith('node'):
                fileobj.contents = node.as_json()
                return fileobj
            elif filepath.endswith('pattern'):
                return fileobj
            raise ztpserver.repository.FileObjectNotFound
        cfg['return_value.get_file'] = Mock(side_effect=get_file)

        m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_HTML)
        self.assertEqual(resp.body, str())

    @patch('ztpserver.controller.create_repository')
    def test_get_definition_wo_validation(self, m_repository):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        definitions_file = create_definition()
        definitions_file.add_action()

        node = create_node()
        cfg = dict()

        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('.node'):
                m_file_object.read.return_value = node.as_dict()
            elif arg.endswith('definition'):
                m_file_object.read.return_value = definitions_file.as_dict()
            else:
                raise ztpserver.repository.FileObjectNotFound
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file
        m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertIsInstance(json.loads(resp.body), dict)

    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_definition_w_validation_success(self, m_load_pattern,
                                                 m_repository):
        node = create_node()

        definitions_file = create_definition()
        definitions_file.add_action()

        cfg = dict()

        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('.node'):
                m_file_object.read.return_value = node.as_dict()
            elif arg.endswith('definition'):
                m_file_object.read.return_value = definitions_file.as_dict()
            elif arg.endswith('attributes'):
                raise ztpserver.repository.FileObjectNotFound
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file

        m_repository.configure_mock(**cfg)

        m_load_pattern.return_value.match_node.return_value = Mock()

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        self.assertIsInstance(json.loads(resp.body), dict)


    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_definition_w_validation_failure(self, m_load_pattern,
                                                 m_repository):
        definitions_file = create_definition()
        definitions_file.add_action()

        serialnumber = random_string()
        node = Mock(serialnumber=serialnumber)
        node.identifier.return_value = serialnumber

        cfg = dict()

        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('.node'):
                m_file_object.read.return_value = node
            elif arg.endswith('definition'):
                m_file_object.read.return_value = definitions_file.as_dict()
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file
        m_repository.configure_mock(**cfg)

        m_load_pattern.return_value.match_node.return_value = False

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_BAD_REQUEST)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_HTML)
        self.assertEqual(resp.body, str())

    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_definition_w_attributes_no_substitution(self, m_load_pattern,
                                                         m_repository):

        node = create_node()

        g_attr_foo = random_string()
        attributes_file = create_attributes()
        attributes_file.add_attribute('variables', {'foo': g_attr_foo})

        l_attr_url = random_string()
        definitions_file = create_definition()
        definitions_file.add_attribute('foo', random_string())
        definitions_file.add_action(name='dummy action',
                                    attributes=dict(url=l_attr_url))

        cfg = dict()
        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('.node'):
                m_file_object.read.return_value = node.as_dict()
            elif arg.endswith('definition'):
                m_file_object.read.return_value = definitions_file.as_dict()
            elif arg.endswith('attributes'):
                m_file_object.read.return_value = attributes_file.as_dict()
            elif arg.endswith('startup-config'):
                raise ztpserver.repository.FileObjectNotFound
            return m_file_object
        cfg['return_value.get_file'] = Mock(side_effect=m_get_file)

        cfg['return_value.match_node.return_value'] = True
        m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')

        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)

        attrs = resp.json['actions'][0]['attributes']
        self.assertFalse('variables' in attrs)
        self.assertFalse('foo' in attrs)
        self.assertEqual(attrs['url'], l_attr_url)

class DefinitionStartupConfigTests(unittest.TestCase):

    @patch('ztpserver.controller.create_repository')
    @patch('ztpserver.controller.load_pattern')
    def test_get_definition_w_startuo_config(self, m_load_pattern,
                                             m_repository):

        node = create_node()

        action_name_1 = random_string()
        action_name_2 = random_string()
        definitions_file = create_definition()
        definitions_file.add_action(action=action_name_1)
        definitions_file.add_action(action=action_name_2,
                                    always_execute=True)

        cfg = dict()

        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('.node'):
                m_file_object.read.return_value = dict(node.as_dict())
            elif arg.endswith('definition'):
                m_file_object.read.return_value = \
                    dict(definitions_file.as_dict())
            elif arg.endswith('attributes'):
                raise ztpserver.repository.FileObjectNotFound
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file
        m_repository.configure_mock(**cfg)
        m_load_pattern.return_value.match_node.return_value = Mock()

        url = '/nodes/%s' % node.serialnumber
        request = Request.blank(url, method='GET')

        resp = request.get_response(ztpserver.controller.Router())
        self.assertEqual(resp.status_code, constants.HTTP_STATUS_OK)
        self.assertEqual(resp.content_type, constants.CONTENT_TYPE_JSON)
        actions = [x['action'] for x in json.loads(resp.body)['actions']]
        self.assertEqual(actions, ['replace_config',
                                   action_name_2])


if __name__ == '__main__':
    enable_logging()
    unittest.main()
