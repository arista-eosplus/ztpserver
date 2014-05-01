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
# pylint: disable=W0622,W0402,W0613
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

    def show(self, request, resource, **kwargs):
        node = self.load_node(resource)
        state = 'get_startup_config_definition' if node else 'http_bad_request'
        return self.fsm(state, resource=resource, node=node)

    def get_config(self, request, resource, **kwargs):
        return self.fsm('get_startup_config_file', resource=resource)

    def fsm(self, next_state, **kwargs):
        log.debug('starting fsm')
        response = self.response()
        while next_state != None:
            log.debug('next_state=%s, current_status=%d',
                      next_state, response.status_code)
            method = getattr(self, next_state)
            (response, next_state) = method(response, **kwargs)
        log.debug('fsm completed, final_status=%d', response.status_code)
        return response

    def load_node(self, resource):
        node = None
        filepath = '%s/%s' % (resource, NODE_FN)
        if self.store.exists(filepath):
            nodeattrs = self.get_file_contents('%s/%s' % (resource, NODE_FN))
            nodeattrs = self.deserialize(nodeattrs, CONTENT_TYPE_YAML)
            node = ztpserver.neighbordb.create_node(nodeattrs)
        else:
            log.debug('node attributes file was not found')
        return node

    def get_startup_config_file(self, response, resource, **kwargs):
        next_state = 'http_bad_request'
        filepath = '%s/%s' % (resource, STARTUP_CONFIG_FN)
        if self.store.exists(filepath):
            response.body = self.get_file_contents(filepath)
            response.content_type = CONTENT_TYPE_OTHER
            next_state = None
        return (response, next_state)

    def required_attributes(self, response, request, node):
        # pylint: disable=R0201
        next_state = 'node_exists'
        req_attrs = ['systemmac']
        if not set(req_attrs).issubset(set(request.json.keys())):
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
                              node.dumps(CONTENT_TYPE_YAML))
        return (response, 'set_location')

    def post_config(self, response, request, node):
        next_state = 'post_node'
        if 'config' in request.json:
            data = request.json.get('config')
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
                            log.debug('definition template does not exist')
                            return (response, 'http_bad_request')
                        data = ndb.create_node_definition(definition, node)
                        data = self.serialize(data, CONTENT_TYPE_YAML)
                    elif filename == PATTERN_FN:
                        data = matches[0].dumps(CONTENT_TYPE_YAML)
                    files.append((filename, data))
                self.add_node(node.systemmac, files)
                response.status = HTTP_STATUS_CREATED
                next_state = 'dump_node'
            else:
                log.debug('No pattern match found for node')
        return (response, next_state)

    def set_location(self, response, request, node):
        # pylint: disable=R0201
        response.location = '/nodes/%s' % node.systemmac
        return (response, None)

    def add_node(self, systemmac, files=None):
        log.debug('Adding node %s to server', systemmac)
        self.store.add_folder(systemmac)
        if files:
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
            contents = self.get_file_contents(filepath)
            contents = self.deserialize(contents, CONTENT_TYPE_YAML)
            response.body = self.serialize(contents, CONTENT_TYPE_JSON)
            response.content_type = CONTENT_TYPE_JSON
            next_state = 'get_attributes'
        return (response, next_state)

    def get_attributes(self, response, resource, node):
        filepath = '%s/%s' % (resource, ATTRIBUTES_FN)
        if self.store.exists(filepath):
            attributes = self.deserialize(self.get_file_contents(filepath),
                                          CONTENT_TYPE_JSON)
            definition = self.deserialize(response.body, CONTENT_TYPE_YAML)
            definition['attributes'].update(attributes)
            response.body = self.serialize(definition, CONTENT_TYPE_JSON)
            log.debug('node attributes loaded')
        return (response, 'do_validation')

    def do_validation(self, response, resource, node):
        next_state = None
        config = ztpserver.config.runtime

        if not config.default.disable_topology_validation:
            next_state = 'http_bad_request'
            try:
                fobj = self.get_file('%s/%s' % (resource, PATTERN_FN))
                if fobj.exists:
                    pattern = ztpserver.neighbordb.load_pattern(fobj.name)
                    if pattern.match_node(node):
                        log.debug('pattern is valid!')
                        next_state = None
            except FileObjectNotFound as exc:
                log.debug('Pattern file not found: %s', exc)
        return (response, next_state)

    def http_bad_request(self, response, *args, **kwargs):
        # pylint: disable=R0201
        ''' return HTTP 400 Bad Request '''

        response.body = ''
        response.content_type = 'text/html'
        response.status = HTTP_STATUS_BAD_REQUEST
        return (response, None)


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
        mapper = routes.Mapper()

        kwargs = dict()

        url = ztpserver.config.runtime.default.server_url
        log.debug('url=%s', url)
        parts = urlparse.urlsplit(url)
        if parts.path:
            path = parts.path[:-1] if parts.path.endswith('/') else parts.path
            if path:
                log.debug("path_prefix is %s", path)
                kwargs['path_prefix'] = path

        log.debug('Creating submapper with kwargs: %s', kwargs)
        with mapper.submapper(**kwargs) as m:

            # configure /bootstrap
            controller = BootstrapController()
            m.connect('bootstrap', '/bootstrap',
                    controller=controller,
                    action='index', conditions=dict(method=['GET']))
            m.connect('bootstrap_config', '/bootstrap/config',
                    controller=controller,
                    action='config', conditions=dict(method=['GET']))

            # configure /nodes
            controller = NodesController()
            m.collection('nodes', 'node',
                        controller=controller,
                        collection_actions=['create'],
                        member_actions=['show'],
                        member_prefix='/{resource}')
            m.connect('node_config', '/nodes/{resource}/startup-config',
                      controller=controller, 
                      action='get_config', conditions=dict(method=['GET']))

            # configure /actions
            m.collection('actions', 'action',
                        controller=ActionsController(),
                        collection_actions=[],
                        member_actions=['show'],
                        member_prefix='/{resource}')

            # configure /files
            m.collection('files', 'file',
                        controller=FilesController(),
                        collection_actions=[],
                        member_actions=['show'],
                        member_prefix='/{resource:.*}')

        super(Router, self).__init__(mapper)



