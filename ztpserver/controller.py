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
# pylint: disable=W0622,W0402,W0613,W0142,R0201
#

import os
import logging
import urlparse

from string import Template

import routes

from webob.static import FileApp

import ztpserver.config
import ztpserver.neighbordb

from ztpserver.wsgiapp import WSGIController, WSGIRouter

from ztpserver.neighbordb import create_node, Node

from ztpserver.repository import create_repository
from ztpserver.repository import FileObjectNotFound, FileObjectError
from ztpserver.constants import HTTP_STATUS_NOT_FOUND, HTTP_STATUS_CREATED
from ztpserver.constants import HTTP_STATUS_BAD_REQUEST, HTTP_STATUS_CONFLICT
from ztpserver.constants import CONTENT_TYPE_JSON, CONTENT_TYPE_PYTHON
from ztpserver.constants import CONTENT_TYPE_YAML, CONTENT_TYPE_OTHER

DEFINITION_FN = 'definition'
STARTUP_CONFIG_FN = 'startup-config'
PATTERN_FN = 'pattern'
NODE_FN = '.node'
ATTRIBUTES_FN = 'attributes'
BOOTSTRAP_CONF = 'bootstrap.conf'

log = logging.getLogger(__name__)    # pylint: disable=C0103

class BaseController(WSGIController):

    FOLDER = None

    def __init__(self, **kwargs):
        data_root = ztpserver.config.runtime.default.data_root
        self.repository = create_repository(data_root)
        super(BaseController, self).__init__()

    def expand(self, *args, **kwargs):
        ''' Returns an expanded filepath relative to data_root '''

        filepath = os.path.join(*args)
        folder = kwargs.get('folder', self.FOLDER)
        return os.path.join(folder, filepath)

    def http_bad_request(self, *args, **kwargs):
        ''' Returns HTTP 400 Bad Request '''

        log.debug('HTTP_BAD_REQUEST')
        return dict(body='', content_type='text/html',
                    status=HTTP_STATUS_BAD_REQUEST)

    def http_not_found(self, *args, **kwargs):
        ''' Returns HTTP 404 Not Found '''

        log.debug('HTTP_NOT_FOUND')
        return dict(body='', content_type='text/html',
                    status=HTTP_STATUS_NOT_FOUND)



class FilesController(BaseController):

    FOLDER = 'files'

    def __repr__(self):
        return 'FilesController(folder=%s)' % self.FOLDER

    def show(self, request, resource, **kwargs):
        ''' Handles GET /files/{resource} '''

        try:
            urlvars = request.urlvars
            if urlvars.get('format') is not None:
                resource += '.%s' % urlvars.get('format')
            log.debug('Requesting file: %s', resource)
            filepath = self.expand(resource)
            filename = self.repository.get_file(filepath).name
            return FileApp(filename)
        except FileObjectNotFound:
            log.error('Requested file %s was not found', resource)
            return self.http_not_found()


class ActionsController(BaseController):

    FOLDER = 'actions'

    def __repr__(self):
        return 'ActionsController(folder=%s)' % self.FOLDER

    def show(self, request, resource, **kwargs):
        ''' Handles GET /actions/{resource} '''

        try:
            log.debug('Requesting action: %s', resource)
            filepath = self.expand(resource)
            body = self.repository.get_file(filepath).read(CONTENT_TYPE_PYTHON)
            return dict(body=body, content_type=CONTENT_TYPE_PYTHON)
        except FileObjectNotFound:
            log.error('Requested action %s was not found', resource)
            return self.http_not_found()


class NodesController(BaseController):

    FOLDER = 'nodes'

    def __repr__(self):
        return 'NodesController(folder=%s)' % self.FOLDER

    def create(self, request, **kwargs):
        try:
            node = create_node(request.json)
        except Exception:       # pylint: disable=W0703
            log.exception('Unable to create node metadata')
            response = self.http_bad_request()
            return self.response(**response)
        return self.fsm('required_attributes', request=request, node=node)

    def show(self, request, resource, *args, **kwargs):
        try:
            fobj = self.repository.get_file(self.expand(resource, NODE_FN))
            node = fobj.read(CONTENT_TYPE_JSON, Node)
            state = 'get_definition'
        except Exception:           # pylint: disable=W0703
            log.exception('Unable to load node metadata')
            response = self.http_bad_request()
            return self.response(**response)
        return self.fsm(state, resource=resource, node=node)

    def get_config(self, request, resource, **kwargs):
        return self.fsm('get_startup_config_file', resource=resource)

    def put_config(self, request, resource, *args, **kwargs):
        return self.fsm('do_put_config', request=request, resource=resource)

    def fsm(self, next_state, **kwargs):
        ''' Execute the FSM for the request '''

        log.debug('FSM starting with state %s', next_state)
        response = dict()
        try:
            while next_state != None:
                log.debug('FSM next_state=%s', next_state)
                method = getattr(self, next_state)
                (response, next_state) = method(response, **kwargs)
            log.debug('FSM completed successfully')
        except Exception:            # pylint: disable=W0703
            log.exception('Unexpected error in FSM')
            response = self.http_bad_request()
        finally:
            log.debug('response: %s', response)
            return response     # pylint: disable=W0150

    def get_startup_config_file(self, response, resource, **kwargs):
        try:
            filename = self.expand(resource, STARTUP_CONFIG_FN)
            response['body'] = self.repository.get_file(filename).read()
            response['content_type'] = CONTENT_TYPE_OTHER
        except FileObjectNotFound:
            log.error('Startup config file was not found')
            raise
        else:
            return (response, None)

    def do_put_config(self, response, **kwargs):
        try:
            body = str(kwargs['request'].body)
            content_type = str(kwargs['request'].content_type)
            filename = self.expand(kwargs['resource'], STARTUP_CONFIG_FN)
            fobj = self.repository.get_file(filename)
        except FileObjectNotFound:
            fobj = self.repository.add_file(filename)
        except Exception:
            log.error('Unable to write startup-config for node')
            raise
        finally:
            fobj.write(body, content_type)
        return (response, None)

    def required_attributes(self, response, *args, **kwargs):
        ''' Checks the initial POST to validate that all required
        values are present
        '''

        req_attrs = ['systemmac']
        request = kwargs.get('request')
        if not set(req_attrs).issubset(set(request.json.keys())):
            log.error('Missing required attributes in request object')
            raise AttributeError
        return (response, 'node_exists')

    def node_exists(self, response, *args, **kwargs):
        next_state = 'post_config'
        systemmac = kwargs.get('node').systemmac

        if self.repository.exists(self.expand(systemmac, DEFINITION_FN)) or \
           self.repository.exists(self.expand(systemmac, STARTUP_CONFIG_FN)):
            log.info('Found node entry for %s', systemmac)
            response['status'] = HTTP_STATUS_CONFLICT
            next_state = 'dump_node'

        return (response, next_state)

    def dump_node(self, response, *args, **kwargs):
        try:
            node = kwargs.get('node')
            contents = node.serialize()
            filename = self.expand(node.systemmac, NODE_FN)
            fobj = self.repository.get_file(filename)
        except FileObjectNotFound:
            fobj = self.repository.add_file(filename)
        except:
            log.error('Unexpected error trying to execute dump_node')
            raise
        finally:
            fobj.write(contents, CONTENT_TYPE_JSON)
        return (response, 'set_location')

    def post_config(self, response, *args, **kwargs):
        try:
            config = kwargs['request'].json['config']
            systemmac = kwargs['node'].systemmac

            self.repository.add_folder(self.expand(systemmac))

            config_fn = self.expand(systemmac, STARTUP_CONFIG_FN)
            self.repository.add_file(config_fn).write(config)

            response['status'] = HTTP_STATUS_CREATED
            next_state = 'set_location'
        except KeyError as exc:
            if exc.message != 'config':
                raise
            log.warning('No config attribute specified in request')
            next_state = 'post_node'
        return (response, next_state)

    def post_node(self, response, *args, **kwargs):
        try:
            node = kwargs['node']
            topology = ztpserver.neighbordb.load_topology()
            # pylint: disable=E1103
            matches = topology.match_node(node)
            log.info('Node matched %d pattern(s)', len(matches))
            match = matches[0]

            definition_url = self.expand(match.definition, folder='definitions')
            fobj = self.repository.get_file(definition_url)
            definition = fobj.read(content_type=CONTENT_TYPE_YAML)
            definition_fn = self.expand(node.systemmac, DEFINITION_FN)

            self.repository.add_folder(self.expand(node.systemmac))

            fobj = self.repository.add_file(definition_fn)
            fobj.write(definition, CONTENT_TYPE_YAML)

            pattern_fn = self.expand(node.systemmac, PATTERN_FN)
            fobj = self.repository.add_file(pattern_fn)
            fobj.write(match.serialize(), CONTENT_TYPE_YAML)

            response['status'] = HTTP_STATUS_CREATED
        except IndexError:
            log.error('Unable to find pattern match for %s', node.systemmac)
            raise
        except FileObjectNotFound as exc:
            # TODO add folder clean up if exception is raised
            log.error('Unable to find file %s', exc.message)
            raise
        except Exception:
            log.error('Unexpected error trying to execute post_node')
            raise
        return (response, 'dump_node')

    def set_location(self, response, *args, **kwargs):
        try:
            node = kwargs.get('node')
            response['location'] = self.expand(node.systemmac)
        except Exception:
            log.error('Unexpected error trying to execute set_location')
            raise
        return (response, None)

    def get_definition(self, response, *args, **kwargs):
        ''' Reads the node specific definition from disk and stores it in the
        repsonse dict with key `definition`
        '''

        try:
            filename = self.expand(kwargs['resource'], DEFINITION_FN)
            log.debug('defintion filename is %s', filename)
            fobj = self.repository.get_file(filename)
            definition = fobj.read(CONTENT_TYPE_YAML)
            response['definition'] = definition
            log.debug('loaded definition from file with %d actions',
                      len(definition['actions']))
        except FileObjectNotFound:
            log.warning('Node definition file does not exist')
        except Exception:
            log.error('Unable to load definition file')
            raise
        return (response, 'do_validation')

    def get_startup_config(self, response, *args, **kwargs):
        try:
            filename = self.expand(kwargs['resource'], STARTUP_CONFIG_FN)
            log.debug('startup-config filename is %s', filename)
            self.repository.get_file(filename)
            response['get_startup_config'] = True
            if 'definition' not in response:
                response['definition'] = dict(name='Autogenerated definition',
                                              actions=list())
            response['definition']['actions'].append(\
                ztpserver.neighbordb.replace_config_action(kwargs['resource'],
                                                           STARTUP_CONFIG_FN))
        except FileObjectNotFound:
            log.warning('Node startup-config file does not exist')
        except Exception:
            log.error('Unable to load startup-config definition file')
            raise
        return (response, 'do_actions')

    def do_actions(self, response, *args, **kwargs):
        try:
            assert 'get_startup_config' in response
            actions = response['definition']['actions']
            _actions = list()
            for action in actions:
                always_execute = action.get('always_execute', False)
                if always_execute:
                    _actions.append(action)
                    log.debug('adding action %s due to always_execute flag',
                              str(action.get('name')))
                else:
                    log.debug('remvoing action %s due to always_execute flag',
                              str(action.get('name')))
            response['definition']['actions'] = _actions
        except AssertionError:
            log.warning('Static startup-config file not found for node')
        return (response, 'get_attributes')

    def do_validation(self, response, *args, **kwargs):
        try:
            config = ztpserver.config.runtime
            if not config.default.disable_topology_validation:
                filename = self.expand(kwargs['resource'], PATTERN_FN)
                log.debug('pattern filename is %s', filename)
                fobj = self.repository.get_file(filename)
                pattern = ztpserver.neighbordb.load_pattern(fobj.name)
                if not pattern.match_node(kwargs['node']):
                    raise Exception('Node failed pattern validation')
                log.info('Node pattern is valid')
            else:
                log.warning('Topology validation is disabled')
        except Exception:
            log.error('Unexpected error trying to execute do_validation')
            raise
        return (response, 'get_startup_config')

    def get_attributes(self, response, *args, **kwargs):
        ''' Reads the resource specific attributes file and stores it in the
        response dict as 'attributes'
        '''
        try:
            filename = self.expand(kwargs['resource'], ATTRIBUTES_FN)
            log.debug('Attributes filename is %s', filename)
            fileobj = self.repository.get_file(filename)
            attributes = fileobj.read(CONTENT_TYPE_YAML)
            response['attributes'] = attributes
            log.debug('loaded %d attributes from file', len(attributes))
        except FileObjectNotFound:
            log.warning('Node specific attributes file does not exist')
            response['attributes'] = dict()
        return (response, 'do_substitution')

    def do_substitution(self, response, *args, **kwargs):
        # pylint: disable=R0914
        try:
            definition = response.get('definition')
            attrs = definition.get('attributes', dict())

            nodeattrs = response.get('attributes', dict())

            def lookup(name):
                log.debug('Lookup up value for variable %s', name)
                return nodeattrs.get(name, attrs.get(name))

            _actions = list()
            for action in definition['actions']:
                log.info('Analyzing action: %s', action.get('name'))
                _attributes = dict()
                for key, value in action.get('attributes').items():
                    try:
                        update = dict()
                        for _key, _value in value.items():
                            if str(_value).startswith('$'):
                                _value = lookup(_value[1:])
                            update[_key] = _value
                    except AttributeError:
                        if str(value).startswith('$'):
                            value = lookup(value[1:])
                        update = value
                    finally:
                        log.debug('%s=%s', key, update)
                        _attributes[key] = update
                action['attributes'] = _attributes
                _actions.append(action)
            definition['actions'] = _actions
            response['definition'] = definition
            log.debug('processed %d actions', len(definition['actions']))
        except Exception:
            log.error('Unable to perform substitution')
            raise
        return (response, 'do_resources')

    def do_resources(self, response, *args, **kwargs):
        try:
            definition = response['definition']
            node = kwargs.get('node')
            _actions = list()
            for action in definition.get('actions'):
                attrs = action.get('attributes', dict())
                action['attributes'] = \
                    ztpserver.neighbordb.resources(attrs, node)
                _actions.append(action)
            definition['actions'] = _actions
            response['definition'] = definition
            log.debug('processed %d actions', len(definition['actions']))
        except Exception:
            log.error('Unable to perform dynamic resource lookups')
            raise
        return (response, 'finalize_response')

    def finalize_response(self, response, *args, **kwargs):
        _response = dict()
        _response['body'] = response['definition']
        _response['status'] = response.get('status', 200)
        _response['content_type'] = response.get('content_type',
                                                 CONTENT_TYPE_JSON)
        return (_response, None)



class BootstrapController(BaseController):

    DEFAULTCONFIG = {
        'logging': list(),
        'xmpp': dict()
    }

    FOLDER = 'bootstrap'

    def __repr__(self):
        return 'BootstrapController(folder=%s)' % self.FOLDER

    def config(self, request, **kwargs):
        ''' Handles GET /bootstrap/config '''

        try:
            filename = self.expand(BOOTSTRAP_CONF)
            body = self.repository.get_file(filename).read(CONTENT_TYPE_YAML)
            resp = dict(body=body, content_type=CONTENT_TYPE_JSON)
        except FileObjectNotFound:
            log.warning('Bootstrap config file not found, returning defaults')
            body = self.DEFAULTCONFIG
            resp = dict(body=body, content_type=CONTENT_TYPE_JSON)
        except FileObjectError:
            log.exception('Unable to retrieve bootstrap config file')
            resp = self.http_bad_request()
        return resp

    def index(self, request, **kwargs):
        ''' Handles GET /bootstrap '''

        try:
            filename = self.expand(ztpserver.config.runtime.bootstrap.filename)
            fobj = self.repository.get_file(filename).read(CONTENT_TYPE_PYTHON)
            default_server = ztpserver.config.runtime.default.server_url
            body = Template(fobj).substitute(SERVER=default_server)
            resp = dict(body=body, content_type=CONTENT_TYPE_PYTHON)
        except KeyError:
            log.debug('Expected variable was not provided')
            resp = self.http_bad_request()
        except (FileObjectNotFound, FileObjectError):
            log.exception('Unable to retrieve bootstrap script')
            resp = self.http_bad_request()
        return resp


class Router(WSGIRouter):
    ''' Routes incoming requests by mapping the URL to a controller '''

    def __init__(self):
        # pylint: disable=E1103,W0142

        mapper = routes.Mapper()

        kwargs = {}

        url = ztpserver.config.runtime.default.server_url
        log.debug('url=%s', url)
        parts = urlparse.urlsplit(url)
        if parts.path:
            path = parts.path[:-1] if parts.path.endswith('/') else parts.path
            if path:
                log.debug('path_prefix is %s', path)
                kwargs['path_prefix'] = path

        log.debug('Creating submapper with kwargs: %s', kwargs)
        with mapper.submapper(**kwargs) as router_mapper:

            # configure /bootstrap
            router_mapper.connect('bootstrap', '/bootstrap',
                                  controller=BootstrapController,
                                  action='index',
                                  conditions=dict(method=['GET']))

            router_mapper.connect('bootstrap_config', '/bootstrap/config',
                                  controller=BootstrapController,
                                  action='config',
                                  conditions=dict(method=['GET']))

            # configure /nodes
            router_mapper.collection('nodes', 'node',
                                     controller=NodesController,
                                     collection_actions=['create'],
                                     member_actions=['show'],
                                     member_prefix='/{resource}')

            router_mapper.connect('get_node_config',
                                  '/nodes/{resource}/startup-config',
                                  controller=NodesController,
                                  action='get_config',
                                  conditions=dict(method=['GET']))

            router_mapper.connect('put_node_config',
                                  '/nodes/{resource}/startup-config',
                                  controller=NodesController,
                                  action='put_config',
                                  conditions=dict(method=['PUT']))

            # configure /actions
            router_mapper.collection('actions', 'action',
                                     controller=ActionsController,
                                     collection_actions=[],
                                     member_actions=['show'],
                                     member_prefix='/{resource}')

            # configure /files
            router_mapper.collection('files', 'file',
                                     controller=FilesController,
                                     collection_actions=[],
                                     member_actions=['show'],
                                     member_prefix='/{resource:.*}')

        super(Router, self).__init__(mapper)

