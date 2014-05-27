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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0102,C0103,E1103,W0142,W0613
#

import unittest
import json

from webob import Request

from mock import MagicMock, Mock, patch

import ztpserver.neighbordb
import ztpserver.topology
import ztpserver.controller
import ztpserver.config
import ztpserver.repository

from ztpserver.controller import DEFINITION_FN, PATTERN_FN

from ztpserver.app import enable_handler_console
from ztpserver.repository import FileObjectNotFound, FileObjectError

from server_test_lib import remove_all, random_string
from server_test_lib import ztp_headers, write_file
from server_test_lib import create_definition, create_attributes, create_node
from server_test_lib import create_bootstrap_conf

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


class BootstrapControllerUnitTests(unittest.TestCase):

    def setUp(self):
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    @patch('string.Template.substitute')
    def test_index_success(self, m_substitute):
        m_substitute.return_value = random_string()

        controller = ztpserver.controller.BootstrapController()
        resp = controller.index(None)

        self.assertTrue(m_substitute.called)
        self.assertEqual(resp['content_type'], 'text/x-python')
        self.assertEqual(resp['body'], m_substitute.return_value)

    def test_index_bootstrap_not_found_failure(self):
        cfg = {'return_value.get_file.side_effect': FileObjectError}
        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.index(None)

        self.assertTrue(resp['status'], 400)
        self.assertEqual(resp['body'], '')

    def test_index_bootstrap_inaccessible_failure(self):
        cfg = {'return_value.read.side_effect': FileObjectError}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.index(None)

        self.assertTrue(resp['status'], 400)
        self.assertEqual(resp['body'], '')

    def test_config_success(self):
        config = create_bootstrap_conf()
        config.add_logging(dict(destination=random_string(),
                                level=random_string()))

        cfg = {'return_value.read.return_value': config.as_dict()}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.config(None)

        self.assertEqual(resp['body'], config.as_dict())
        self.assertEqual(resp['content_type'], 'application/json')

    def test_config_defaults(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.config(None)

        self.assertEqual(resp['body'], controller.DEFAULTCONFIG)
        self.assertEqual(resp['content_type'], 'application/json')

    def test_config_failure(self):
        cfg = {'return_value.read.side_effect': FileObjectError}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.BootstrapController()
        resp = controller.config(None)

        self.assertEqual(resp['body'], '')
        self.assertEqual(resp['status'], 400)


class BootstrapControllerIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    @patch('string.Template.substitute')
    def test_get_bootstrap_success(self, m_substitute):
        contents = random_string()
        m_substitute.return_value = contents

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')
        self.assertEqual(resp.body, contents)

    def test_get_bootstrap_missing(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, 'text/html')

    @patch('string.Template.substitute')
    def test_get_bootstrap_misconfigured(self, m_substitute):
        m_substitute.side_effect = KeyError

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, 'text/html')

    def test_get_bootstrap_inaccessible(self):
        cfg = {'return_value.get_file.side_effect': FileObjectError}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap', headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, 'text/html')

    def test_get_bootstrap_config_success(self):
        config = create_bootstrap_conf()
        config.add_logging(dict(destination=random_string(),
                                level=random_string()))

        cfg = {'return_value.read.return_value': config.as_dict()}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        request = Request.blank('/bootstrap/config')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(json.loads(resp.body), config.as_dict())

    def test_get_bootstrap_config_defaults(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        request = Request.blank('/bootstrap/config')
        resp = request.get_response(ztpserver.controller.Router())

        defaultconfig = {'logging': list(), 'xmpp': dict()}

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(json.loads(resp.body), defaultconfig)

class FilesControllerIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    def tearDown(self):
        remove_all()

    def test_get_file_success(self):
        contents = random_string()
        filepath = write_file(contents)

        self.m_repository.return_value.get_file.return_value.name = filepath

        url = '/files/%s' % filepath
        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        self.m_repository.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.body, contents)


    def test_get_missing_file(self):
        cfg = {'return_value.get_file.side_effect':
                    ztpserver.repository.FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        filename = random_string()
        url = '/files/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        filepath = 'files/%s' % filename
        self.m_repository.return_value.get_file.assert_called_with(filepath)
        self.assertEqual(resp.status_code, 404)


class ActionsControllerIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    def test_get_action_success(self):
        contents = random_string()
        cfg = {'return_value.read.return_value': contents}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        filename = random_string()
        url = '/actions/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        self.m_repository.return_value.get_file.assert_called_with(url[1:])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')
        self.assertEqual(resp.body, contents)

    def test_get_action_missing(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        filename = random_string()
        url = '/actions/%s' % filename

        request = Request.blank(url)
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 404)


class NodesControllerUnitTests(unittest.TestCase):

    def setUp(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    def test_required_attributes_success(self):
        request = Mock(json={'systemmac': random_string()})
        response = dict()

        controller = ztpserver.controller.NodesController()
        resp = controller.required_attributes(response, request=request)

        self.assertEqual(resp, (dict(), 'node_exists'))

    def test_required_attributes_missing(self):
        controller = ztpserver.controller.NodesController()
        self.assertRaises(AttributeError, controller.required_attributes,
                          None, None)

    def test_node_exists_success(self):
        self.m_repository.return_value.exists.return_value = True

        node = Mock(systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node)

        self.assertEqual(state, 'dump_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], 409)

    def test_node_exists_definition_exists(self):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(DEFINITION_FN):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node)

        self.assertEqual(state, 'dump_node')
        self.assertEqual(resp['status'], 409)

    def test_node_exists_startup_config_exists(self):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(ztpserver.controller.STARTUP_CONFIG_FN):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node)

        self.assertEqual(state, 'dump_node')
        self.assertEqual(resp['status'], 409)

    def test_node_exists_sysmac_folder_exists(self):
        node = create_node()
        cfg = dict()

        def m_exists(arg):
            if arg.endswith(node.systemmac):
                return True
            return False
        cfg['return_value.exists.side_effect'] = m_exists

        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node)

        self.assertEqual(state, 'post_config')
        self.assertTrue('status' not in resp)

    def test_node_exists_failure(self):
        self.m_repository.return_value.exists.return_value = False

        node = Mock(systemmac=random_string())
        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.node_exists(dict(), node=node)

        self.assertEqual(state, 'post_config')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    def test_dump_node_success(self):
        node = Mock(systemmac=random_string())

        cfg = dict()
        cfg['return_value.get_file'] = Mock()
        self.m_repository.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.dump_node(dict(), node=node)

        self.assertEqual(state, 'set_location')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    def test_dump_node_write_file_failure(self):

        cfg = {'return_value.get_file.return_value.write.side_effect': \
               ztpserver.repository.FileObjectError}
        self.m_repository.configure_mock(**cfg)

        node = Mock(systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        self.assertRaises(ztpserver.repository.FileObjectError,
                          controller.dump_node,
                          dict(),
                          node=node)

    def test_set_location_success(self):
        node = Mock(systemmac=random_string())
        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.set_location(dict(), node=node)

        location = 'nodes/%s' % node.systemmac
        self.assertIsNone(state)
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['location'], location)

    def test_set_location_failure(self):
        controller = ztpserver.controller.NodesController()
        self.assertRaises(AttributeError, controller.set_location,
                          dict(), node=None)

    def test_post_config_success(self):
        request = Mock(json=dict(config=random_string()))
        node = Mock(systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_config(dict(), request=request,
                                               node=node)

        self.assertEqual(state, 'set_location')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], 201)

    def test_post_config_key_error_failure(self):
        request = Mock(json=dict())
        node = Mock(systemmac=random_string())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_config(dict(), request=request,
                                               node=node)

        self.assertEqual(state, 'post_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, dict())

    def test_post_config_failure(self):
        controller = ztpserver.controller.NodesController()
        self.assertRaises(Exception, controller.post_config, dict())

    def test_post_node_success_single_match(self):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(systemmac=random_string())

        m_load = Mock()
        m_load.return_value.match_node.return_value = [Mock()]
        ztpserver.neighbordb.load = m_load

        controller = ztpserver.controller.NodesController()

        (resp, state) = controller.post_node(dict(), request=request, node=node)

        self.assertEqual(state, 'dump_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], 201)

    def test_post_node_success_multiple_matches(self):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(systemmac=random_string())

        m_load = Mock()
        m_load.return_value.match_node.return_value = [Mock(), Mock(), Mock()]
        ztpserver.neighbordb.load = m_load

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.post_node(dict(), request=request, node=node)

        self.assertEqual(state, 'dump_node')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status'], 201)

    def test_post_node_failure_no_matches(self):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(systemmac=random_string())

        m_load = Mock()
        m_load.return_value.match_node.return_value = list()
        ztpserver.neighbordb.load = m_load

        controller = ztpserver.controller.NodesController()
        self.assertRaises(IndexError, controller.post_node, dict(),
                          request=request, node=node)

    def test_post_node_no_definition_in_pattern(self):
        request = Mock(json=dict(neighbors=dict()))
        node = Mock(systemmac=random_string())

        pattern = Mock()
        del pattern.definition

        m_load = Mock()
        m_load.return_value.match_node.return_value = [pattern]
        ztpserver.neighbordb.load = m_load

        controller = ztpserver.controller.NodesController()
        self.assertRaises(AttributeError, controller.post_node, dict(),
                          request=request, node=node)

    def test_get_definition_success(self):
        cfg = {'return_value.read.return_value': MagicMock()}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_definition(dict(),
                                                  resource=random_string())

        self.assertEqual(state, 'do_validation')
        self.assertIsInstance(resp, dict)

    def test_get_startup_config_success(self):
        ztpserver.neighbordb.replace_config_action = Mock(return_value=dict())

        response = dict(definition={'actions': list()})

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_startup_config(response,
                                                      resource=random_string())

        self.assertEqual(state, 'do_actions')
        self.assertIsInstance(resp, dict)

    def test_get_startup_config_success_no_definition(self):
        resource = random_string()

        action_name = random_string()
        action = {'name': action_name, 'action': 'replace_config'}
        ztpserver.neighbordb.replace_config_action = Mock(return_value=action)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_startup_config(dict(), resource=resource)

        self.assertEqual(state, 'do_actions')
        self.assertIsInstance(resp, dict)
        self.assertTrue(resp['get_startup_config'])
        self.assertTrue(resp['definition'], 'Autogenerated definition')
        self.assertEqual(resp['definition']['actions'][0]['name'], action_name)

    def test_do_validation_success(self):
        ztpserver.neighbordb.load_pattern = Mock()

        cfg = {'return_value.match_node.return_value': True}
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

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
        (resp, state) = controller.do_validation(dict())

        self.assertEqual(state, 'get_startup_config')
        self.assertIsInstance(resp, dict)

    def test_get_attributes_success(self):
        cfg = {'return_value.read.return_value': random_string()}
        self.m_repository.return_value.get_file.configure_mock(**cfg)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_attributes(dict(),
                                                  resource=random_string())

        self.assertEqual(state, 'do_substitution')
        self.assertIsInstance(resp, dict)

    def test_get_attributes_missing(self):
        node = create_node()

        self.m_repository.return_value.exists.return_value = False
        self.m_repository.return_value.get_file = \
            Mock(side_effect=ztpserver.repository.FileObjectNotFound)


        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.get_attributes(dict(),
                                                  resource=node.systemmac)

        self.assertEqual(state, 'do_substitution')
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['attributes'], dict())

    def test_do_substitution_success(self):


        defattrs = dict(foo='$foo')

        definition = create_definition()
        definition.add_attribute('foo', 'bar')
        definition.add_action(name='dummy action', attributes=defattrs)

        response = dict(definition=definition.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_substitution(response)

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
        (resp, state) = controller.do_substitution(response)

        self.assertEqual(state, 'do_resources')
        self.assertIsInstance(resp, dict)

        foo = resp['definition']['actions'][0]['attributes']['foo']
        self.assertEqual(foo, g_attr_foo)

    def test_do_resources_success(self):


        var_foo = random_string()
        ztpserver.neighbordb.resources = Mock(return_value=dict(foo=var_foo))

        definition = create_definition()
        definition.add_action(name='dummy action',
                              attributes=dict(foo=random_string()))

        response = dict(definition=definition.as_dict())

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_resources(response, node=Mock())

        self.assertEqual(state, 'finalize_response')
        self.assertIsInstance(resp, dict)
        foo = resp['definition']['actions'][0]['attributes']['foo']
        self.assertEqual(foo, var_foo)

    def test_do_put_config_success(self):


        resource = random_string()
        body = random_string()
        request = Mock(content_type='text/plain', body=body)

        controller = ztpserver.controller.NodesController()
        (resp, state) = controller.do_put_config(dict(), resource=resource,
                                                 request=request)

        self.assertIsNone(state)
        self.assertEqual(resp, dict())

class NodesControllerPostFsmIntegrationTests(unittest.TestCase):

    def setUp(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')
        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    def test_missing_required_attributes(self):
        url = '/nodes'
        body = json.dumps(dict())

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())

        resp = request.get_response(ztpserver.controller.Router())
        self.assertEqual(resp.status_code, 400)

    def test_node_exists(self):
        url = '/nodes'
        systemmac = random_string()
        body = json.dumps(dict(systemmac=systemmac))

        self.m_repository.return_value.exists.return_value = True

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % systemmac

        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.location, location)

    def test_post_config(self):
        url = '/nodes'
        systemmac = random_string()
        config = random_string()
        body = json.dumps(dict(systemmac=systemmac, config=config))

        self.m_repository.return_value.exists.return_value = False

        request = Request.blank(url, body=body, method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        location = 'http://localhost/nodes/%s' % systemmac
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.location, location)

    def test_post_node_success(self):
        node = create_node()

        definition = create_definition()
        definition.add_action()

        cfg = {'return_value.exists.return_value': False}

        self.m_repository.configure_mock(**cfg)

        cfg = {'return_value.match_node.return_value': [Mock()]}
        ztpserver.neighbordb.load = Mock()
        ztpserver.neighbordb.load.configure_mock(**cfg)

        request = Request.blank('/nodes', body=node.as_json(), method='POST',
                                headers=ztp_headers())
        resp = request.get_response(ztpserver.controller.Router())

        args_list = list()
        args_list.append('nodes/%s/%s' % (node.systemmac, DEFINITION_FN))
        args_list.append('nodes/%s/%s' % (node.systemmac, PATTERN_FN))

        for arg in args_list:
            self.m_repository.return_value.add_file.assert_any_call(arg)

        location = 'http://localhost/nodes/%s' % node.systemmac
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.location, location)


class NodesControllerGetFsmIntegrationTests(unittest.TestCase):

    def setUp(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', False, 'default')

        self.m_repository = Mock()
        ztpserver.controller.create_repository = self.m_repository

    def test_get_fsm_missing_node(self):
        cfg = {'return_value.get_file.side_effect': FileObjectNotFound}
        self.m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % random_string()
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)


    def test_get_startup_config_wo_validation(self):
        ztpserver.config.runtime.set_value(\
            'disable_topology_validation', True, 'default')

        ztpserver.neighbordb.load_pattern = Mock()
        ztpserver.neighbordb.create_node = Mock()

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

        self.m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertIsInstance(json.loads(resp.body), dict)

    def test_get_startup_config_w_validation_success(self):
        ztpserver.neighbordb.create_node = Mock()

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
            elif arg.endswith('pattern'):
                fileobj.return_value.read.return_value = random_string()
            else:
                raise ztpserver.repository.FileObjectNotFound
            return fileobj
        cfg['return_value.get_file'] = Mock(side_effect=m_get_file)

        self.m_repository.configure_mock(**cfg)

        cfg = {'return_value.match_node.return_value': True}
        ztpserver.neighbordb.load_pattern = Mock()
        ztpserver.neighbordb.load_pattern.configure_mock(**cfg)

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertIsInstance(json.loads(resp.body), dict)

    def test_get_startup_config_w_validation_failure(self):
        m_load_pattern = Mock()
        m_load_pattern.return_value.match_node.return_value = list()
        ztpserver.neighbordb.load_pattern = m_load_pattern

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

        self.m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, 'text/html')
        self.assertEqual(resp.body, str())

    def test_get_definition_wo_validation(self):
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

        self.m_repository.configure_mock(**cfg)

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertIsInstance(json.loads(resp.body), dict)

    def test_get_definition_w_validation_success(self):
        node = create_node()

        definitions_file = create_definition()
        definitions_file.add_action()

        cfg = dict()

        def m_get_file(arg):
            m_file_object = Mock()
            if arg.endswith('definition'):
                m_file_object.read.return_value = definitions_file.as_dict()
            elif arg.endswith('attributes'):
                raise ztpserver.repository.FileObjectNotFound
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file

        self.m_repository.configure_mock(**cfg)

        m_load_pattern = Mock()
        m_load_pattern.return_value.match_node.return_value = Mock()
        ztpserver.neighbordb.load_pattern = m_load_pattern

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertIsInstance(json.loads(resp.body), dict)


    def test_get_definition_w_validation_failure(self):
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
            return m_file_object

        cfg['return_value.get_file.side_effect'] = m_get_file

        self.m_repository.configure_mock(**cfg)

        m_load_pattern = Mock()
        m_load_pattern.return_value.match_node.return_value = [Mock()]
        ztpserver.neighbordb.load_pattern = m_load_pattern

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, 'text/html')
        self.assertEqual(resp.body, str())

    def test_get_definition_w_attributes_no_substitution(self):
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
        self.m_repository.configure_mock(**cfg)

        ztpserver.neighbordb.load_pattern = Mock()

        url = '/nodes/%s' % node.systemmac
        request = Request.blank(url, method='GET')
        resp = request.get_response(ztpserver.controller.Router())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        attrs = resp.json['actions'][0]['attributes']
        self.assertFalse('variables' in attrs)
        self.assertFalse('foo' in attrs)
        self.assertEqual(attrs['url'], l_attr_url)

if __name__ == '__main__':
    unittest.main()

