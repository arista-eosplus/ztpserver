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

import logging
import urlparse

from string import Template

import routes

import webob.static

import ztpserver.wsgiapp
import ztpserver.config
import ztpserver.neighbordb

from ztpserver.serializers import SerializerError
from ztpserver.repository import create_file_store
from ztpserver.repository import FileObjectNotFound, FileObjectError
from ztpserver.constants import HTTP_STATUS_NOT_FOUND, HTTP_STATUS_OK
from ztpserver.constants import HTTP_STATUS_BAD_REQUEST, HTTP_STATUS_CONFLICT
from ztpserver.constants import CONTENT_TYPE_JSON, CONTENT_TYPE_PYTHON
from ztpserver.constants import CONTENT_TYPE_YAML, CONTENT_TYPE_OTHER
from ztpserver.constants import HTTP_STATUS_CREATED

DEFINITION_FN = 'definition'
STARTUP_CONFIG_FN = 'startup-config'
PATTERN_FN = 'pattern'
NODE_FN = '.node'
ATTRIBUTES_FN = 'attributes'
BOOTSTRAP_CONF = 'bootstrap.conf'

log = logging.getLogger(__name__)    # pylint: disable=C0103

class StoreController(ztpserver.wsgiapp.Controller):

    def __init__(self, name, **kwargs):
        path_prefix = kwargs.get('path_prefix')
        self.store = self.create_filestore(name, path_prefix=path_prefix)
        super(StoreController, self).__init__()

    @classmethod
    def create_filestore(cls, name, path_prefix=None):
        try:
            store = create_file_store(name, basepath=path_prefix)

        except ztpserver.repository.FileStoreError:
            log.warn('could not create FileStore due to invalid path')
            store = None
        return store

    def get_file(self, filename):
        return self.store.get_file(filename)

    def get_file_contents(self, filename):
        try:
            return self.get_file(filename).contents
        except (FileObjectNotFound, FileObjectError):
            return None

class FilesController(StoreController):

    def __init__(self):
        prefix = ztpserver.config.runtime.files.path_prefix
        folder = ztpserver.config.runtime.files.folder
        super(FilesController, self).__init__(folder, path_prefix=prefix)

    def __repr__(self):
        return 'FilesController'

    def show(self, request, resource, **kwargs):
        urlvars = request.urlvars
        if urlvars.get('format') is not None:
            resource += '.%s' % urlvars.get('format')

        try:
            obj = self.get_file(resource)

        except ztpserver.repository.FileObjectNotFound:
            log.debug('Requested file was not found')
            return dict(status=HTTP_STATUS_NOT_FOUND)

        return webob.static.FileApp(obj.name)

class ActionsController(StoreController):

    def __init__(self):
        prefix = ztpserver.config.runtime.actions.path_prefix
        folder = ztpserver.config.runtime.actions.folder
        super(ActionsController, self).__init__(folder, path_prefix=prefix)

    def show(self, request, resource, **kwargs):
        log.debug('Requesting action: %s', resource)

        if not self.store.exists(resource):
            log.debug('Requested action not found')
            return dict(status=HTTP_STATUS_NOT_FOUND)

        return dict(status=HTTP_STATUS_OK,
                    content_type=CONTENT_TYPE_PYTHON,
                    body=self.get_file_contents(resource))


class NodesController(StoreController):

    def __init__(self):
        self.definitions = self.create_filestore('definitions')
        super(NodesController, self).__init__('nodes')

    def __repr__(self):
        return 'NodesController'

    def create(self, request, **kwargs):
        node = ztpserver.neighbordb.create_node(request.json)
        return self.fsm('required_attributes', request=request, node=node)

    def show(self, request, resource, *args, **kwargs):
        try:
            node = self.load_node(resource)
            state = 'get_definition'
        except Exception:           # pylint: disable=W0703
            log.error('There was an error trying to load the node definition')
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
        except Exception as exc:            # pylint: disable=W0703
            log.exception(exc)
            response = self.http_bad_request()
        finally:
            log.debug('response: %s', response)
            return self.response(**response)      # pylint: disable=W0150

    def load_node(self, resource, *args, **kwargs):
        ''' Returns a :py:class:`ztpserver.topology.Node` instance

        :param resource: system mac in string format of node
        '''
        try:
            filepath = '%s/%s' % (resource, NODE_FN)
            log.debug('Loading node from %s', filepath)
            attrs = self.deserialize(self.store.get_file(filepath).contents,
                                     CONTENT_TYPE_YAML)
            node = ztpserver.neighbordb.create_node(attrs)
        except Exception:
            log.error('Unable to load node object!')
            raise
        return node

    def get_startup_config_file(self, response, resource, **kwargs):
        next_state = 'http_bad_request'
        filepath = '%s/%s' % (resource, STARTUP_CONFIG_FN)
        if self.store.exists(filepath):
            response['body'] = self.get_file_contents(filepath)
            response['content_type'] = CONTENT_TYPE_OTHER
            next_state = None
        return (response, next_state)

    def do_put_config(self, response, **kwargs):
        try:
            request = kwargs['request']
            assert request.content_type == CONTENT_TYPE_OTHER
            filepath = '%s/%s' % (kwargs['resource'], STARTUP_CONFIG_FN)
            self.store.write_file(filepath, request.body)
        except AssertionError:
            log.error('Invalid content-type specified for PUT method')
            raise
        except Exception:
            log.error('Unable to write startup-config for node')
            raise
        return (response, None)

    def required_attributes(self, response, *args, **kwargs):
        ''' Checks the initial POST to validate that all required
        values are present
        '''

        # pylint: disable=R0201
        next_state = 'node_exists'
        req_attrs = ['systemmac']
        request = kwargs.get('request')
        if not set(req_attrs).issubset(set(request.json.keys())):
            log.error('Missing required attributes in request')
            raise AttributeError
        return (response, next_state)

    def node_exists(self, response, *args, **kwargs):
        next_state = 'post_config'
        node = kwargs.get('node')

        valid = lambda x: self.store.exists('%s/%s' % (x, DEFINITION_FN)) or \
                          self.store.exists('%s/%s' % (x, STARTUP_CONFIG_FN))

        if valid(node.systemmac):
            response['status'] = HTTP_STATUS_CONFLICT
            next_state = 'dump_node'

        return (response, next_state)

    def dump_node(self, response, *args, **kwargs):
        try:
            node = kwargs.get('node')
            self.store.write_file('%s/%s' % (node.systemmac, NODE_FN),
                                  node.dumps(CONTENT_TYPE_YAML))
        except Exception:
            log.error('Unable to write node metadata')
            raise
        else:
            return (response, 'set_location')

    def post_config(self, response, *args, **kwargs):
        try:
            request = kwargs.get('request')
            config = request.json['config']
            node = kwargs.get('node')
            self.add_node(node.systemmac, [('startup-config', config)])
            response['status'] = HTTP_STATUS_CREATED
            next_state = 'set_location'
        except KeyError as exc:
            if exc.message != 'config':
                raise
            log.warning('No config attribute specified in request')
            next_state = 'post_node'
        return (response, next_state)

    def post_node(self, response, *args, **kwargs):
        ndb = ztpserver.neighbordb
        try:
            request = kwargs['request']
            assert 'neighbors' in request.json
            node = kwargs['node']
            matches = ndb.topology.match_node(node)
            assert matches

            fileset = list()
            url = matches[0].definition

            fileset.append((DEFINITION_FN,
                            self.definitions.get_file(url).contents))

            fileset.append((PATTERN_FN,
                            matches[0].dumps(CONTENT_TYPE_YAML)))

            self.add_node(node.systemmac, fileset)

            response['status'] = HTTP_STATUS_CREATED
            next_state = 'dump_node'
        except Exception:
            log.error('Unable to create node definition')
            raise
        return (response, next_state)

    def set_location(self, response, *args, **kwargs):
        try:
            node = kwargs.get('node')
            response['location'] = '/nodes/%s' % node.systemmac
        except Exception:
            log.error('Unable to set HTTP Location header')
            raise
        return (response, None)

    def add_node(self, systemmac, files=None):
        log.debug('Adding node %s to server', systemmac)
        self.store.add_folder(systemmac)
        if files:
            for filename, contents in files:
                filepath = '%s/%s' % (systemmac, filename)
                self.store.write_file(filepath, contents)

    def get_definition(self, response, *args, **kwargs):
        ''' Reads the node specific definition from disk and stores it in the
        repsonse dict with key `definition`
        '''

        try:
            filepath = '%s/%s' % (kwargs['resource'], DEFINITION_FN)
            log.debug('defintion filepath is %s', filepath)
            assert self.store.exists(filepath)
            fileobj = self.store.get_file(filepath)
            definition = self.deserialize(fileobj.contents, CONTENT_TYPE_YAML)
            response['definition'] = definition
            log.debug('loaded definition from file with %d actions',
                      len(definition['actions']))
        except AssertionError:
            log.warning('Node definition file does not exist')
        except Exception:
            log.error('Unable to load definition file')
            raise
        return (response, 'do_validation')

    def get_startup_config(self, response, *args, **kwargs):
        try:
            filepath = '%s/%s' % (kwargs['resource'], STARTUP_CONFIG_FN)
            log.debug('startup-config filepath is %s', filepath)
            assert self.store.exists(filepath)
            response['get_startup_config'] = True
            if 'definition' not in response:
                response['definition'] = dict(name='Autogenerated definition',
                                              actions=list())
            response['definition']['actions'].append(\
                ztpserver.neighbordb.replace_config_action(kwargs['resource'],
                                                           STARTUP_CONFIG_FN))
        except AssertionError:
            log.warning('Node startup-config file does not exist')
        except Exception:
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
        config = ztpserver.config.runtime
        try:
            if not config.default.disable_topology_validation:
                filepath = '%s/%s' % (kwargs['resource'], PATTERN_FN)
                log.debug('pattern filepath is %s', filepath)
                fileobj = self.store.get_file(filepath)
                pattern = ztpserver.neighbordb.load_pattern(fileobj.name)
                if not pattern.match_node(kwargs['node']):
                    raise Exception('Node failed pattern validation')
                log.info('Node pattern is valid')
            else:
                log.warning('Topology validation is disabled')
        except Exception:
            log.error('Unable to validate node pattern')
            raise
        return (response, 'get_startup_config')

    def get_attributes(self, response, *args, **kwargs):
        ''' Reads the resource specific attributes file and stores it in the
        response dict with key 'attributes'
        '''
        try:
            filepath = '%s/%s' % (kwargs['resource'], ATTRIBUTES_FN)
            log.debug('attributes filepath is %s', filepath)
            fileobj = self.store.get_file(filepath)
            response['attributes'] = self.deserialize(fileobj.contents,
                                                      CONTENT_TYPE_YAML)
            log.debug('loaded %d attributes from file', \
                len(response['attributes']))
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
        _response['body'] = self.serialize(response['definition'],
                                           CONTENT_TYPE_JSON)
        _response['status'] = response.get('status', 200)
        _response['content_type'] = response.get('content_type',
                                                 CONTENT_TYPE_JSON)
        return (_response, None)

    def http_bad_request(self, *args, **kwargs):
        ''' return HTTP 400 Bad Request '''

        log.debug('HTTP_BAD_REQUEST')
        response = dict()
        response['body'] = ''
        response['content_type'] = 'text/html'
        response['status'] = HTTP_STATUS_BAD_REQUEST
        return response


class BootstrapController(StoreController):

    DEFAULTCONFIG = {
        'logging': list(),
        'xmpp': dict()
    }

    def __init__(self):
        prefix = ztpserver.config.runtime.bootstrap.path_prefix
        folder = ztpserver.config.runtime.bootstrap.folder
        super(BootstrapController, self).__init__(folder, path_prefix=prefix)

    def __repr__(self):
        return 'BootstrapController'

    def get_bootstrap(self):
        ''' Returns the bootstrap script '''

        try:
            filename = ztpserver.config.runtime.bootstrap.filename
            data = self.deserialize(self.get_file_contents(filename),
                                    CONTENT_TYPE_PYTHON)

        except ztpserver.repository.FileObjectNotFound as exc:
            log.debug(exc)
            data = None

        return data

    def get_config(self):
        ''' returns the full bootstrap configuration as a dict '''

        try:
            data = self.get_file_contents(BOOTSTRAP_CONF)
            if data is None:
                contents = self.DEFAULTCONFIG
            else:
                contents = self.deserialize(data, CONTENT_TYPE_YAML)

        except SerializerError as exc:
            log.debug(exc)
            contents = None

        return contents

    def config(self, request, **kwargs):
        # pylint: disable=W0613
        log.debug('requesting bootstrap config')
        conf = self.get_config()
        if not conf:
            resp = dict(status=HTTP_STATUS_BAD_REQUEST)
        else:
            resp = dict(body=conf, content_type=CONTENT_TYPE_JSON)
        return resp

    def index(self, request, **kwargs):
        try:
            bootstrap = self.get_bootstrap()
            if not bootstrap:
                log.warn('bootstrap script does not exist')
                return dict(status=HTTP_STATUS_BAD_REQUEST)

            default_server = ztpserver.config.runtime.default.server_url
            body = Template(bootstrap).substitute(SERVER=default_server)
            resp = dict(body=body, content_type=CONTENT_TYPE_PYTHON)

        except ztpserver.repository.FileObjectNotFound as exc:
            log.exception(exc)
            resp = dict(status=HTTP_STATUS_NOT_FOUND)

        except KeyError:
            log.debug('Expected varialble was not provided')
            resp = dict(status=HTTP_STATUS_BAD_REQUEST)

        return resp



class Router(ztpserver.wsgiapp.Router):
    ''' handles incoming requests by mapping urls to controllers '''

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
            controller = BootstrapController()
            router_mapper.connect('bootstrap',
                                  '/bootstrap',
                                  controller=controller,
                                  action='index',
                                  conditions=dict(method=['GET']))

            router_mapper.connect('bootstrap_config', '/bootstrap/config',
                                  controller=controller,
                                  action='config',
                                  conditions=dict(method=['GET']))

            # configure /nodes
            controller = NodesController()
            router_mapper.collection('nodes',
                                     'node',
                                     controller=controller,
                                     collection_actions=['create'],
                                     member_actions=['show'],
                                     member_prefix='/{resource}')

            router_mapper.connect('get_node_config',
                                  '/nodes/{resource}/startup-config',
                                  controller=controller,
                                  action='get_config',
                                  conditions=dict(method=['GET']))

            router_mapper.connect('put_node_config',
                                  '/nodes/{resource}/startup-config',
                                  controller=controller,
                                  action='put_config',
                                  conditions=dict(method=['PUT']))

            # configure /actions
            router_mapper.collection('actions',
                                     'action',
                                     controller=ActionsController(),
                                     collection_actions=[],
                                     member_actions=['show'],
                                     member_prefix='/{resource}')

            # configure /files
            router_mapper.collection('files',
                                     'file',
                                     controller=FilesController(),
                                     collection_actions=[],
                                     member_actions=['show'],
                                     member_prefix='/{resource:.*}')

        super(Router, self).__init__(mapper)

