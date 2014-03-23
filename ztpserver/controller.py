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
import logging

from string import Template

import routes

import webob.static

import ztpserver.wsgiapp
import ztpserver.config
import ztpserver.repository
import ztpserver.data

from ztpserver.constants import *

FILESTORES = {
    "actions": {
        "collection_name": "actions",
        "resource_name": "action",
        "member_prefix": "/{id}",
        "collection_actions": [],
        "member_actions": ['show']
    },
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

class NodeController(StoreController):

    REQ_FIELDS = ['systemmac']

    def __init__(self):
        self.definitions = self._create_filestore('definitions')
        super(NodeController, self).__init__('nodes')

    def __repr__(self):
        return 'NodeController'

    def show(self, request, id, **kwargs):

        # check if startup-config exists
        if self.store.exists('%s/startup-config' % id):
            filepath = '%s/startup-config' % id
            response = dict(body=self.get_file_contents(filepath),
                            content_type=CONTENT_TYPE_OTHER)

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
                # this needs to validate pattern
                pattern = self.get_file_contents(filepath)
                pattern = self.deserialize(pattern, CONTENT_TYPE_YAML)

                if self.store.exists('%s/topology' % id):
                    filepath = '%s/topology' % id
                    neighbors = self.get_file_contents(filepath)
                    neighbors = self.deserialize(neighbors, CONTENT_TYPE_JSON)

                nodeattrs = dict(systemmac=id)
                nodeattrs['neighbors'] = neighbors or dict()
                node = self.create_node_object(nodeattrs)

                if not self.match_pattern(pattern, node):
                    log.info("node %s failed to match existing pattern" % id)
                    return dict(status=HTTP_STATUS_BAD_REQUEST)

            response = dict(body=definition, content_type=CONTENT_TYPE_JSON)

        else:
            log.info("requested node id %s not found" % id)
            response = dict(status=HTTP_STATUS_NOT_FOUND)

        return response

    def create(self, request, **kwargs):

        if not self._validate_request(request.json):
            log.debug("POST request is missing required fields")
            return dict(status=HTTP_STATUS_BAD_REQUEST)

        node = self.create_node_object(request.json)

        # check if the node exists and return 409 if it does
        if self.store.exists(node.systemmac):
            log.debug("node already exists")
            return dict(status=HTTP_STATUS_CONFLICT)

        if 'config' in request.json:
            location = self.add_node(node, request.json)
            response = dict(status=HTTP_STATUS_CREATED, location=location)

        elif 'neighbors' in request.json:
            filepath = ztpserver.config.runtime.db.neighbordb
            neighbordb = self._load_neighbordb(filepath)
            if neighbordb is None:
                log.error('could not load neighbordb (%s)' % filepath)
                return dict(status=HTTP_STATUS_BAD_REQUEST)

            patterns = neighbordb.get_node_patterns(node.systemmac)

            matches = self.match_patterns(patterns, node)
            log.info("found %d pattern matches" % len(matches))

            if not matches:
                log.info("unable to match any valid pattern")
                response = dict(status=HTTP_STATUS_BAD_REQUEST)

            else:
                # create node resource using first pattern match
                log.info("creating node definition with pattern %s" %
                    matches[0].name)
                location = self.add_node(node, request.json, pattern=matches[0])
                response = dict(status=HTTP_STATUS_CREATED, location=location)

        else:
            log.info('unable to handle POST')
            response = dict(status=HTTP_STATUS_BAD_REQUEST)

        return response

    def _validate_request(self, req):
        return set(self.REQ_FIELDS).issubset(set(req.keys()))

    def _load_neighbordb(self, filename):
        # pylint: disable=R0201
        database = ztpserver.data.NeighborDb()
        database.load(filename)
        return database

    def add_node(self, node, request, **kwargs):

        self.store.add_folder(node.systemmac)

        if 'config' in request:
            filename = '%s/startup-config'
            contents = kwargs.get('config')

        if 'neighbors' in request and 'pattern' in kwargs:
            pattern = kwargs.get('pattern')
            neighbors = request.get('neighbors')

            definition = self.definitions.get_file(pattern.definition)
            definition = self.deserialize(definition.contents,
                                          CONTENT_TYPE_YAML)

            definition.setdefault('attributes',
                                  self._process_attributes(definition))

            filename = '%s/definition' % node.systemmac
            contents = self.serialize(definition)

            self.store.write_file('%s/pattern' % node.systemmac,
                                  self.serialize(pattern, CONTENT_TYPE_JSON))

            self.store.write_file('%s/topology' % node.systemmac,
                                  self.serialize(neighbors, CONTENT_TYPE_JSON))

        self.store.write_file(filename, contents)
        return '/nodes/%s' % node.systemmac

    def _process_attributes(self, definition):
        # TODO finish definition of function
        return definition.get('attributes') or dict()

    def create_node_object(self, nodeattrs):
        # pylint: disable=R0201
        # create node object
        node = ztpserver.data.Node(**nodeattrs)   # pylint: disable=W0142
        node.systemmac = str(node.systemmac).replace(':', '')

        neighbors = nodeattrs.get('neighbors')
        if neighbors:
            # add interfaces and neighbors
            for interface, neighbors in nodeattrs['neighbors'].items():
                obj = node.add_interface(interface)
                for neighbor in neighbors:
                    obj.add_neighbor(neighbor['device'], neighbor['port'])

        return node

    def match_patterns(self, patterns, node):
        matches = list()
        for pattern in patterns:
            log.debug('try to match pattern %s' % pattern.name)
            result = self.match_pattern(pattern, node)
            if result:
                matches.append(pattern)
            else:
                log.debug('pattern does not match')
        return matches

    def match_pattern(self, pattern, node):
        interfaces = node.interfaces()
        result = dict()

        for items in pattern.interfaces:
            for entry in items:
                # pattern specifies nothing connected but we have a neighbor
                # on the specified interfaces so the rule is violated
                if entry.node is None and entry.interface in interfaces:
                    log.info("pattern failed due to 'none' interface present")
                    return None

                # pattern specifies any connected but we did not find a
                # neighbor on the specified interface so the rule is violated
                elif entry.node == 'any' and entry.interface not in interfaces:
                    log.info("failed due to 'any' interface not present")
                    return None

                # pattern specifices no connected neighbor and interface is
                # not present so the rule is matches
                if entry.node is None and entry.interface not in interfaces:
                    log.debug("pattern matched on 'none' for interface %s" % \
                        entry.interface)
                    result[entry.interface] = None

                else:
                    matches = self.match_interface_pattern(entry, node)
                    if matches is None:
                        log.info("failed to match %s" % entry.interface)
                        return None
                    result[entry.interface] = matches
                    log.info("pattern %s matches %s" % (entry.interface, matches))

                # remove the interface as an available match from the set
                # of interfaces
                # TODO this should probably be a set not a list
                interfaces = [x for x in interfaces if x not in matches]
        return result

    def match_interface_pattern(self, pattern, node):
        # pylint: disable=R0201
        if pattern.interface == 'any':
            for interface in node.interfaces():
                neighbors = node.interfaces(interface).neighbors
                for neighbor in neighbors:
                    node_match = pattern.match_device(neighbor.device)
                    port_match = pattern.match_port(neighbor.port)
                    if node_match and port_match:
                        return [interface]
                    else:
                        log.debug("port match results for %s (node=%s, port=%s)" % \
                            (neighbor, node_match, port_match))
            matches = None
        else:
            matches = pattern.match_interfaces(node.interfaces())
        return matches


class BootstrapController(StoreController):

    DEFAULTCONFIG = {
        "logging": list(),
        "xmpp": dict()
    }

    def __init__(self):
        super(BootstrapController, self).__init__('bootstrap')

    def __repr__(self):
        return "BootstrapController"

    def get_bootstrap(self):
        """ Returns the bootstrap script """

        try:
            filename = ztpserver.config.runtime.default.bootstrap_file
            data = self.deserialize(self.get_file_contents(filename),
                                    CONTENT_TYPE_PYTHON)

        except ztpserver.repository.FileObjectNotFound as exc:
            log.exception(exc)
            data = None

        return data

    def get_config(self):
        """ returns the full bootstrap configuration as a dict """

        data = self.get_file_contents('bootstrap.conf')
        contents = self.deserialize(data, CONTENT_TYPE_YAML)

        return contents or self.DEFAULTCONFIG

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
        mapper.collection('nodes', 'node',
                          controller=NodeController(),
                          collection_actions=['create'],
                          member_actions=['show'])

        # configure filestores
        for filestore, kwargs in FILESTORES.items():
            controller = FileStoreController(filestore)
            mapper.collection(controller=controller, **kwargs)   # pylint: disable=W0142

        super(Router, self).__init__(mapper)



