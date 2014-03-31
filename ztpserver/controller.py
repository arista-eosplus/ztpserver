# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=W1201
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
import logging

from string import Template

import routes

import webob.static

import ztpserver.wsgiapp
import ztpserver.config
import ztpserver.repository

from ztpserver.topology import neighbordb
from ztpserver.constants import *

FILESTORES = {
    "packages": {
        "collection_name": "packages",
        "resource_name": "package",
        "member_prefix": "/{id}",
        "collection_actions": [],
        "member_actions": ['show']
    },
    "files": {
        "collection_name": "files",
        "resource_name": "file",
        "member_prefix": "/{id:.*}",
        "collection_actions": [],
        "member_actions": ['show']
    }
}

log = logging.getLogger(__name__)    # pylint: disable=C0103

class StoreController(ztpserver.wsgiapp.Controller):

    def __init__(self, name, **kwargs):
        path_prefix = kwargs.get('path_prefix')
        self.store = self._create_filestore(name, path_prefix=path_prefix)
        super(StoreController, self).__init__()

    def _create_filestore(self, name, path_prefix=None):
        # pylint: disable=R0201

        try:
            store = ztpserver.repository.create_file_store(name, path_prefix)
        except ztpserver.repository.FileStoreError:
            log.warn('could not create FileStore due to invalid path')
            store = None
        return store

    def get_file(self, filename):
        return self.store.get_file(filename)

    def get_file_contents(self, filename):
        return self.get_file(filename).contents


class FileStoreController(StoreController):

    def __repr__(self):
        return "FileStoreController"

    def show(self, request, id, **kwargs):
        urlvars = request.urlvars
        filename = urlvars.get('id')
        if urlvars.get('format') is not None:
            filename += '.%s' % urlvars.get('format')

        try:
            obj = self.get_file(filename)

        except ztpserver.repository.FileObjectNotFound:
            return dict(status=HTTP_STATUS_NOT_FOUND)

        return webob.static.FileApp(obj.name)

class ActionsController(StoreController):

    def __init__(self):
        prefix = ztpserver.config.runtime.actions.path_prefix
        folder = ztpserver.config.runtime.actions.folder
        super(ActionsController, self).__init__(folder, path_prefix=prefix)

    def show(self, request, id, **kwargs):
        log.debug("Requesting action: %s" % id)
        if not self.store.exists(id):
            log.debug("Requested action not found")
            return dict(status=HTTP_STATUS_NOT_FOUND)

        return dict(status=HTTP_STATUS_OK,
                    content_type=CONTENT_TYPE_PYTHON,
                    body=self.get_file_contents(id))



class NodeController(StoreController):

    REQ_FIELDS = ['systemmac']

    def __init__(self):
        self.definitions = self._create_filestore('definitions')
        super(NodeController, self).__init__('nodes')

    def __repr__(self):
        return 'NodeController'

    def getconfig(self, request, id, **kwargs):
        log.debug('Sending startup-config contents to node %s' % id)
        filepath = '%s/startup-config' % id
        if not self.store.exists(filepath):
            response = dict(status=HTTP_STATUS_BAD_REQUEST)
        else:
            response = dict(body=self.get_file_contents(filepath),
                            content_type=CONTENT_TYPE_OTHER)
        return response

    def show(self, request, id, **kwargs):

        # check if startup-config exists
        if self.store.exists('%s/startup-config' % id):
            log.debug("Sending startup-config definition to node %s" % id)
            url = '%s/nodes/%s/startup-config' % \
                (ztpserver.config.runtime.default.server_url, str(id))
            response = self.startup_config_definition(url)

        # check if definition exists
        elif self.store.exists('%s/definition' % id):
            filepath = '%s/definition' % id
            definition = self.deserialize(self.get_file_contents(filepath),
                                          CONTENT_TYPE_YAML)

            # update attributes with node static attributes
            if self.store.exists('%s/attributes' % id):
                filepath = '%s/attributes' % id
                attributes = self.deserialize(self.get_file_contents(filepath),
                                              CONTENT_TYPE_YAML)
                definition['attributes'].update(attributes)

            if self.store.exists('%s/pattern' % id) and \
                not ztpserver.config.runtime.default.disable_pattern_checks:

                filepath = '%s/pattern' % id
                contents = self.get_file_contents(filepath)
                attrs = self.deserialize(contents, CONTENT_TYPE_JSON)
                pattern = ztpserver.topology.Pattern(**attrs)

                if self.store.exists('%s/topology' % id):
                    filepath = '%s/topology' % id
                    neighbors = self.get_file_contents(filepath)
                    neighbors = self.deserialize(neighbors, CONTENT_TYPE_JSON)

                nodeattrs = dict(systemmac=id)
                nodeattrs['neighbors'] = neighbors or dict()
                node = ztpserver.topology.create_node(nodeattrs)

                if not self.match_pattern(pattern, node):
                    log.debug("node %s failed to match existing pattern" % id)
                    return dict(status=HTTP_STATUS_BAD_REQUEST)

            response = dict(body=definition, content_type=CONTENT_TYPE_JSON)

        else:
            log.debug("requested node id %s not found" % id)
            response = dict(status=HTTP_STATUS_NOT_FOUND)

        log.debug("NodeController response: %s" % response)
        return response

    def create(self, request, **kwargs):

        if not set(self.REQ_FIELDS).issubset(set(request.json.keys())):
            log.debug("POST request is missing required fields")
            return dict(status=HTTP_STATUS_BAD_REQUEST)

        node = ztpserver.topology.create_node(request.json)

        # check if the node exists and return 409 if it does
        if self.store.exists(node.systemmac):
            log.debug("node already exists")
            return dict(status=HTTP_STATUS_CONFLICT)

        if 'config' in request.json:
            location = self.add_node(node, request.json)
            response = dict(status=HTTP_STATUS_CREATED, location=location)

        elif 'neighbors' in request.json:
            if neighbordb is None:
                return dict(status=HTTP_STATUS_BAD_REQUEST)

            matches = neighbordb.match_node(node)
            log.debug("Found %d pattern matches" % len(matches))
            log.debug("Matched patterns: %s" % [x.name for x in matches])

            if not matches:
                log.debug("Unable to match any valid pattern")
                response = dict(status=HTTP_STATUS_BAD_REQUEST)

            else:
                # create node resource using first pattern match
                log.debug("Creating node definition with pattern %s" %
                    matches[0].name)
                location = self.add_node(node, request.json, pattern=matches[0])
                response = dict(status=HTTP_STATUS_CREATED, location=location)

        else:
            log.debug('unable to handle POST')
            response = dict(status=HTTP_STATUS_BAD_REQUEST)

        return response

    def add_node(self, node, request, **kwargs):

        if ztpserver.config.runtime.default.disable_node_creation:
            log.debug("Skipping node creation for node %s due to disable_node_creation=True" \
                % node)
            return '/nodes/%s' % node.systemmac

        self.store.add_folder(node.systemmac)

        if 'config' in request:
            filename = '%s/startup-config' % node.systemmac
            contents = request.get('config')

        if 'neighbors' in request and 'pattern' in kwargs:
            pattern = kwargs.get('pattern')
            neighbors = request.get('neighbors')

            definition = self.definitions.get_file(pattern.definition)
            definition = self.deserialize(definition.contents,
                                          CONTENT_TYPE_YAML)

            definition.setdefault('attributes', dict())

            filename = '%s/definition' % node.systemmac
            contents = self.serialize(definition)

            self.store.write_file('%s/pattern' % node.systemmac,
                                  self.serialize(pattern, CONTENT_TYPE_JSON))

            self.store.write_file('%s/topology' % node.systemmac,
                                  self.serialize(neighbors, CONTENT_TYPE_JSON))

        self.store.write_file(filename, contents)
        return '/nodes/%s' % node.systemmac

    def startup_config_definition(self, url):
        """ manually build a definition with a single action replace_config

        :param url: the url pointing to the startup-config file

        """

        action = dict(name='install config',
                      description='install static startup configuration',
                      action='replace_config',
                      attributes=[])

        definition = dict(name='install startup-config',
                          actions=[action],
                          attributes={'replace_config-url': url})

        return dict(body=definition, content_type=CONTENT_TYPE_JSON)


class BootstrapController(StoreController):

    DEFAULTCONFIG = {
        "logging": list(),
        "xmpp": dict()
    }

    def __init__(self):
        prefix = ztpserver.config.runtime.bootstrap.path_prefix
        folder = ztpserver.config.runtime.bootstrap.folder
        super(BootstrapController, self).__init__(folder, path_prefix=prefix)

    def __repr__(self):
        return "BootstrapController"

    def get_bootstrap(self):
        """ Returns the bootstrap script """

        try:
            filename = ztpserver.config.runtime.bootstrap.filename
            data = self.deserialize(self.get_file_contents(filename),
                                    CONTENT_TYPE_PYTHON)

        except ztpserver.repository.FileObjectNotFound as exc:
            log.debug(exc)
            data = None

        return data

    def get_config(self):
        """ returns the full bootstrap configuration as a dict """

        try:
            data = self.get_file_contents('bootstrap.conf')
            contents = self.deserialize(data, CONTENT_TYPE_YAML)

        except ztpserver.repository.FileObjectNotFound:
            log.debug("Bootstrap config file not found...using defaults")
            contents = self.DEFAULTCONFIG

        return contents

    def config(self, request, **kwargs):
        # pylint: disable=W0613
        log.debug("requesting bootstrap config")
        return dict(body=self.get_config(), content_type=CONTENT_TYPE_JSON)

    def index(self, request, **kwargs):
        try:
            bootstrap = self.get_bootstrap()
            if not bootstrap:
                log.warn('bootstrap script does not exist')
                return dict(status=HTTP_STATUS_BAD_REQUEST)

            # TODO need to capture and log an error if substitution fails
            default_server = ztpserver.config.runtime.default.server_url
            body = Template(bootstrap).safe_substitute(SERVER=default_server)

            resp = dict(body=body, content_type=CONTENT_TYPE_PYTHON)

        except ztpserver.repository.FileObjectNotFound as exc:
            log.exception(exc)
            resp = dict(status=HTTP_STATUS_NOT_FOUND)

        return resp



class Router(ztpserver.wsgiapp.Router):
    """ handles incoming requests by mapping urls to controllers """

    def __init__(self):
        mapper = routes.Mapper()

        # configure /bootstrap
        bootstrap = mapper.submapper(controller=BootstrapController())
        bootstrap.connect('bootstrap', '/bootstrap', action='index')
        bootstrap.connect('bootstrap_config',
                          '/bootstrap/config',
                          action='config')

        # configure /nodes
        controller = NodeController()
        mapper.collection('nodes', 'node',
                          controller=controller,
                          collection_actions=['create'],
                          member_actions=['show'])

        nodeconfig = mapper.submapper(controller=controller)
        nodeconfig.connect('nodeconfig', '/nodes/{id}/startup-config',
                           action='getconfig')

        # configure /actions
        mapper.collection('actions', 'action',
                          controller=ActionsController(),
                          collection_actions=[],
                          member_actions=['show'])

        # configure filestores
        for filestore, kwargs in FILESTORES.items():
            controller = FileStoreController(filestore)
            mapper.collection(controller=controller, **kwargs)   # pylint: disable=W0142

        super(Router, self).__init__(mapper)



