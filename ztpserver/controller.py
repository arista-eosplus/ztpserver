# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=W1201,W0622,W0402
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
import logging
import routes
import webob.static

from string import Template

import ztpserver.wsgiapp
import ztpserver.config
import ztpserver.neighbordb

from ztpserver.serializers import SerializerError
from ztpserver.repository import create_file_store, FileObjectNotFound
from ztpserver.constants import HTTP_STATUS_NOT_FOUND, HTTP_STATUS_OK
from ztpserver.constants import HTTP_STATUS_BAD_REQUEST, HTTP_STATUS_CONFLICT
from ztpserver.constants import CONTENT_TYPE_JSON, CONTENT_TYPE_PYTHON
from ztpserver.constants import CONTENT_TYPE_YAML, CONTENT_TYPE_OTHER
from ztpserver.constants import HTTP_STATUS_CREATED

DEFINITION_FN = 'definition'
STARTUP_CONFIG_FN = 'startup-config'
PATTERN_FN = 'pattern'
NODE_FN = 'node'
ATTRIBUTES_FN = 'attributes'

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
        return self.get_file(filename).contents


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
        log.debug('Requesting action: %s' % resource)

        if not self.store.exists(resource):
            log.debug('Requested action not found')
            return dict(status=HTTP_STATUS_NOT_FOUND)

        return dict(status=HTTP_STATUS_OK,
                    content_type=CONTENT_TYPE_PYTHON,
                    body=self.get_file_contents(resource))


class NodeController(StoreController):

    def __init__(self):
        self.definitions = self.create_filestore('definitions')
        super(NodeController, self).__init__('nodes')

    def __repr__(self):
        return 'NodeController'

    def create(self, request, **kwargs):
        node = ztpserver.neighbordb.create_node(request.json)
        return self.fsm('required_attributes', request=request, node=node)

    def show(self, request, resource, **kwargs):
        nodeattrs = self.get_file_contents('%s/%s' % (resource, NODE_FN))
        nodeattrs = self.deserialize(nodeattrs, CONTENT_TYPE_JSON)
        node = ztpserver.neighbordb.create_node(nodeattrs)

        return self.fsm('get_startup_config_definition',
                        resource=resource,
                        node=node)

    def show_config(self, request, resource, **kwargs):
        return self.fsm('get_startup_config_file', resource=resource)

    def fsm(self, next_state, **kwargs):
        log.debug('starting fsm')
        response = self.response()
        while next_state != None:
            log.debug('next_state=%s' % next_state)
            method = getattr(self, next_state)
            (response, next_state) = method(response, **kwargs)
        log.debug('fsm completed')
        return response

    def get_startup_config_file(self, response, resource, **kwargs):
        next_state = 'http_bad_request'
        filepath = '%s/%s' % (resource, STARTUP_CONFIG_FN)
        if self.store.exists(filepath):
            response.body = self.get_file_contents(filepath)
            response.content_type = CONTENT_TYPE_OTHER
            next_state = None
        return (response, next_state)

    def required_attributes(self, response, request, node):
        next_state = 'node_exists'
        REQ_ATTRS = ['systemmac']
        if not set(REQ_ATTRS).issubset(set(request.json.keys())):
            next_state = 'http_bad_request'
        return (response, next_state)

    def node_exists(self, response, request, node):
        next_state = 'post_config'
        if self.store.exists(node.systemmac):
            response.status = HTTP_STATUS_CONFLICT
            next_state = 'dump_node'
        return (response, next_state)

    def dump_node(self, response, request, node):
        self.store.write_file('%s/%s' % (node.systemmac, NODE_FN),
                              node.dumps(CONTENT_TYPE_JSON))
        return (response, 'set_location')

    def post_config(self, response, request, node):
        next_state = 'post_node'
        if 'config' in request.json:
            data = request.get('config')
            self.add_node(node.systemmac, [('startup-config', data)])
            response.status = HTTP_STATUS_CREATED
            next_state = 'set_location'
        return (response, next_state)

    def post_node(self, response, request, node):
        next_state = 'http_bad_request'
        ndb = ztpserver.neighbordb
        if 'neighbors' in request.json:
            matches = ndb.topology.match_node(node)
            if matches:
                files = list()
                for filename in [DEFINITION_FN, PATTERN_FN]:
                    if filename == DEFINITION_FN:
                        try:
                            url = matches[0].definition
                            definition = self.definitions.get_file(url)
                            definition = self.deserialize(definition.contents,
                                                          CONTENT_TYPE_YAML)
                        except FileObjectNotFound:
                            log.debug("definition template does not exist")
                            return (response, 'http_bad_request')
                        data = ndb.create_node_definition(definition, node)
                        data = self.serialize(data, CONTENT_TYPE_JSON)
                    elif filename == PATTERN_FN:
                        data = matches[0].dumps()
                    files.append((filename, data))
                self.add_node(node.systemmac, files)
                response.status = HTTP_STATUS_CREATED
                next_state = 'dump_node'
        return (response, next_state)

    def set_location(self, response, request, node):
        response.location = '/nodes/%s' % node.systemmac
        return (response, None)

    def add_node(self, systemmac, files=[]):
        self.store.add_folder(systemmac)
        for filename, contents in files:
            filepath = '%s/%s' % (systemmac, filename)
            self.store.write_file(filepath, contents)

    def get_startup_config_definition(self, response, resource, node):
        next_state = 'get_definition'
        if self.store.exists('%s/%s' % (resource, STARTUP_CONFIG_FN)):
            cfg = ztpserver.neighbordb.startup_config(resource)
            cfg = self.serialize(cfg, CONTENT_TYPE_JSON)
            response.body = cfg
            response.content_type = CONTENT_TYPE_JSON
            next_state = 'do_validation'
        return (response, next_state)

    def get_definition(self, response, resource, node):
        next_state = 'http_bad_request'
        filepath = '%s/%s' % (resource, DEFINITION_FN)
        if self.store.exists(filepath):
            response.body = self.get_file_contents(filepath)
            response.content_type = CONTENT_TYPE_JSON
            next_state = 'get_attributes'
        return (response, next_state)

    def get_attributes(self, response, resource, node):
        filepath = '%s/%s' % (resource, ATTRIBUTES_FN)
        if self.store.exists(filepath):
            attributes = self.deserialize(self.get_file_contents(filepath),
                                          CONTENT_TYPE_JSON)
            definition = response.json
            definition['attributes'].update(attributes)
            response.body = self.serialize(definition, CONTENT_TYPE_JSON)
        return (response, 'do_validation')

    def do_validation(self, response, resource, node):
        next_state = None
        config = ztpserver.config.runtime

        if not config.default.disable_topology_validation:
            next_state = 'http_bad_request'
            fobj = self.get_file('%s/%s' % (resource, PATTERN_FN))
            pattern = ztpserver.neighbordb.load_pattern(fobj.name)

            topology = self.get_file_contents('%s/node' % resource)
            topology = self.deserialize(topology, CONTENT_TYPE_JSON)

            if pattern.match_node(node):
                next_state = None

        return (response, next_state)

    def http_bad_request(self, response, *args, **kwargs):
        ''' return HTTP 400 Bad Request '''

        response.body = ''
        response.content_type = 'text/html'
        response.status = HTTP_STATUS_BAD_REQUEST
        return (response, None)

    def create_node_definition(self, url, node):
        ''' Creates the node specific definition file based on the
        definition template found at url.  The node definition file
        is created in /nodes/{systemmac}/definition.
        '''

        neighbordb = ztpserver.neighbordb
        log.debug('Creating node definition with url %s' % url)

        definition = self.definitions.get_file(url)
        definition = self.deserialize(definition.contents, CONTENT_TYPE_YAML)

        definition.setdefault('name', 'Autogenerated using %s' % url)
        definition.setdefault('attributes', dict())
        definition['attributes']['ztps_server'] = \
            ztpserver.config.runtime.default.server_url

        # pass the attributes through the resources function in
        # order to convert the global attributes from functions
        # to node specific values
        attributes = definition.get('attributes') or dict()
        definition['attributes'] = neighbordb.resources(attributes, node)

        # iterate through the list of actions to convert any
        # action specific attribute functions to node specific
        # values
        _actions = list()
        for action in definition.get('actions'):
            log.debug('Processing attributes for action %s' % action['name'])
            if 'attributes' in action:
                action['attributes'] = \
                    neighbordb.resources(action['attributes'], node)
            _actions.append(action)
        definition['actions'] = _actions

        # return the serialized node specific definition
        return self.serialize(definition, CONTENT_TYPE_JSON)


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
            data = self.get_file_contents('bootstrap.conf')
            contents = self.deserialize(data, CONTENT_TYPE_JSON)

        except (FileObjectNotFound, SerializerError) as exc:
            log.debug(exc)
            contents = self.DEFAULTCONFIG

        return contents

    def config(self, request, **kwargs):
        # pylint: disable=W0613
        log.debug('requesting bootstrap config')
        return dict(body=self.get_config(), content_type=CONTENT_TYPE_JSON)

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
        mapper = routes.Mapper()

        # configure /bootstrap
        bootstrap = mapper.submapper(controller=BootstrapController())
        bootstrap.connect('bootstrap', '/bootstrap',
                          action='index', conditions=dict(method=['GET']))
        bootstrap.connect('bootstrap_config', '/bootstrap/config',
                          action='config', conditions=dict(method=['GET']))

        # configure /nodes
        controller = NodeController()
        mapper.collection('nodes', 'node',
                          controller=controller,
                          collection_actions=['create'],
                          member_actions=['show'],
                          member_prefix='/{resource}')

        nodeconfig = mapper.submapper(controller=controller)
        nodeconfig.connect('nodeconfig', '/nodes/{resource}/startup-config',
                           action='get_config')

        # configure /actions
        mapper.collection('actions', 'action',
                          controller=ActionsController(),
                          collection_actions=[],
                          member_actions=['show'],
                          member_prefix='/{resource}')

        # configure /files
        mapper.collection('files', 'file',
                          controller=FilesController(),
                          collection_actions=[],
                          member_actions=['show'],
                          member_prefix='/{resource:.*}')

        super(Router, self).__init__(mapper)


