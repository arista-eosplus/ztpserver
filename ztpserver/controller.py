#
# Copyright (c) 2013, Arista Networks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import logging

from string import Template

import routes

import webob.static

import ztpserver.wsgiapp
import ztpserver.config
import ztpserver.repository
import ztpserver.data
from ztpserver.serializers import Serializer

COLLECTIONS = {
    "actions": {
        "collection_name": "actions",
        "resource_name": "action",
        "member_prefix": "/{id}",
        "collection_actions": [],
        "member_actions": ['show']
    },
    "objects": {
        "collection_name": "objects",
        "resource_name": "object",
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

log = logging.getLogger(__name__)
log.info('starting ztpserver.controller')

serializer = Serializer()

class StoreController(ztpserver.wsgiapp.Controller):

    def __init__(self, name, **kwargs):
        path_prefix = kwargs.get('path_prefix')
        self.store = self._create_filestore(name, path_prefix=path_prefix)
        super(StoreController, self).__init__()

    def _create_filestore(self, name, path_prefix=None):
        """ attempts to create a filestore with the given name """

        try:
            filestore = ztpserver.repository.create_file_store(name, path_prefix)
        except ztpserver.repository.FileStoreError:
            log.warn('could not create FileStore due to invalid path')
            filestore = None
        return filestore

class FileStoreController(StoreController):

    def __repr__(self):
        return "FileStoreController"

    def show(self, request, id, **kwargs):

        urlvars = request.urlvars
        fn = urlvars.get('id')
        if urlvars.get('format') is not None:
            fn += '.%s' % urlvars.get('format')

        try:
            obj = self.store.get_file(fn)

        except ztpserver.repository.FileObjectNotFound:
            return webob.exc.HTTPNotFound()

        return webob.static.FileApp(obj.name)

class NodeController(StoreController):

    REQ_FIELDS = [ 'systemmac' ]

    def __init__(self):
        self.definitions = self._create_filestore('definitions')
        super(NodeController, self).__init__('nodes')

    def __repr__(self):
        return 'NodeController'

    def show(self, request, id, **kwargs):
        pass

    def update(self, request, id, **kwargs):
        pass

    def create(self, request, **kwargs):

        if not self._validate_request(request.json):
            log.debug("NodeController.create: missing required fields")
            return webob.exc.HTTPBadRequest('missing required fields')

        node = self._create_node(request.json)
        identifier = node.systemmac

        if self.store.exists(node.systemmac):
            log.debug("NodeController.create: node already exists")
            return webob.exc.HTTPConflict('node already exists')

        if 'config' in request.json.keys():
            path = self.store.add_folder(identifier)
            filename = '%s/startup-config' % identifier
            self.store.write_file(filename, request.json['config'])
            location = '/nodes/%s' % identifier
            headers = [('Location', location)]
            return webob.exc.HTTPCreated(headers=headers)

        elif 'neighbors' in request.json.keys():
            neighbordb = self._load_neighbordb(ztpserver.config.runtime.db.neighbordb)
            patterns = self._get_patterns(neighbordb, node.systemmac)

            matches = self._match_patterns(patterns, node)
            log.info("found %d pattern matches" % len(matches))

            # create node resource using first pattern match
            if matches:
                log.debug("creating node definition with pattern %s" %
                    matches[0].name)
                self._create_node_definition(node, matches[0].definition)
                location = '/nodes/%s' % node.systemmac
                headers = [('Location', location)]
                return webob.exc.HTTPCreated(headers=headers)

        # create node using default definition, if it exists
        elif ztpserver.config.runtime.default.defintion:
            pass

        return webob.exc.HTTPBadRequest()

    def _validate_request(self, req):
        return set(self.REQ_FIELDS).issubset(set(req.keys()))

    def _load_neighbordb(self, filename):
        db = ztpserver.data.NeighborDb()
        db.load(filename)
        return db

    def _get_patterns(self, db, nodeid):
        if nodeid in db.patterns['nodes'].keys():
            log.debug("found node specific entry in neighbordb")
            return [db.patterns['nodes'].get(nodeid)]
        else:
            log.debug("attempting to match non-specific patterns")
            return db.patterns['globals'].values()

    def _create_node_definition(self, node, definition_url):
        log.debug("definition_url is %s" % definition_url)

        definition = self.definitions.get_file('definition')
        log.debug(definition.contents)


    def _create_node(self, req):

        # create node object
        node = ztpserver.data.Node(**req)
        node.systemmac = str(node.systemmac).replace(':', '')

        if 'neighbors' in req.keys():
            # add interfaces and neighbors
            for interface, neighbors in req.get('neighbors').items():
                obj = node.add_interface(interface)
                for neighbor in neighbors:
                    obj.add_neighbor(neighbor['device'], neighbor['port'])

        return node

    def _match_patterns(self, patterns, node):
        """ attempts to match the requesting node to a pattern entry

        :param patterns: the list of patterns to attempt to match
        :param node: the node object of type :py:class:`ztpserver.data.Node`

        """

        matches = list()
        for pattern in patterns:
            result = self._validate_pattern(pattern, node)

            if result is None:
                log.info("Pattern %s does not match node %s" % \
                    (pattern.name, node.systemmac))

            else:
                log.info("Pattern %s matches node %s" % \
                    (pattern.name, node.systemmac))
                matches.append(pattern)

        return matches

    def _validate_pattern(self, pattern, node):
        """ validates a pattern against a set of interfaces

        :param pattern: object of type :py:class:`ztpserver.data.Pattern`
                        to validate against
        :param node: the set of interfaces available from the
                      object of type :py:class:`ztpserver.data.Node`

        """

        interfaces = node.interfaces()
        log.debug("start validation of %s with interfaces %s" % \
            (pattern.name, ','.join(interfaces)))

        result = dict()
        for interface_pattern in pattern.interfaces:

            if interface_pattern.node is None and \
                interface_pattern.interface in interfaces:
                log.debug("pattern failed due to 'none' interface present")
                return None

            elif interface_pattern.node == 'any' and \
                interface_pattern.interface not in interfaces:
                log.debug("failed due to 'any' interface not present")
                return None

            else:
                matches = self._validate_interface_pattern(interface_pattern, node)

                if matches is None:
                    log.debug("failed to match %s" % interface_pattern.interface)
                    return None

                else:
                    result[interface_pattern.interface] = matches
                    interfaces = [x for x in interfaces if x not in matches]

                log.debug("pattern %s matches %s" % \
                    (interface_pattern.interface, matches))

        return result

    def _validate_interface_pattern(self, pattern, node):
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

        filename = ztpserver.config.runtime.default.bootstrap_file
        bootstrap = self.store.get_file(filename)
        return serializer.deserialize(bootstrap.contents, 'text/x-python')

    def get_config(self):
        """ returns the full bootstrap configuration as a dict """

        conf = self.store.get_file('bootstrap.conf')
        if conf.exists:
            contents = serializer.deserialize(conf.contents, 'application/json')
        else:
            log.warn("bootstrap.conf file is missing")
            contents = self.DEFAULTCONFIG
        return contents

    def config(self, request, **kwargs):
        log.debug("requesting bootstrap config")
        body = serializer.serialize(self.get_config(), 'application/json')
        headers = [('Content-Type', 'application/json')]
        return webob.Response(status=200, body=body, headers=headers)

    def index(self, request, **kwargs):
        try:
            bootstrap = self.get_bootstrap()
            if not bootstrap:
                log.warn('bootstrap script does not exist')
                return webob.exc.HTTPBadRequest()

            default_server = ztpserver.config.runtime.default.server_url
            body = Template(bootstrap).safe_substitute(DEFAULT_SERVER=default_server)
            headers = [('Content-Type', 'text/x-python')]
            resp = webob.Response(status=200, body=body, headers=headers)
        except ztpserver.repository.FileObjectNotFound:
            resp = webob.exc.HTTPNotFound()
        return resp



class Router(ztpserver.wsgiapp.Router):
    """ handles incoming requests by mapping urls to controllers """

    def __init__(self):
        mapper = routes.Mapper()

        bootstrap = mapper.submapper(controller=BootstrapController())
        bootstrap.connect('bootstrap', '/bootstrap', action='index')
        bootstrap.connect('bootstrap_config', '/bootstrap/config', action='config')

        mapper.collection('nodes', 'node',
                          controller=NodeController(),
                          collection_actions=['create'],
                          member_actions=['show', 'update'])

        for filestore, kwargs in COLLECTIONS.items():
            controller = FileStoreController(filestore)
            mapper.collection(controller=controller, **kwargs)

        super(Router, self).__init__(mapper)



