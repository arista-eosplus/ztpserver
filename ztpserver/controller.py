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
        self.store = self._create_filestore(name, path_prefix=kwargs.get('path_prefix'))
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

    def __init__(self):
        super(NodeController, self).__init__('nodes')

    def __repr__(self):
        return 'NodeController'

    def update(self, request, id, **kwargs):
        pass

    def create(self, request, **kwargs):
        pass

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
                return webob.exc.HTTPInternalServerError()

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
                          member_actions=['update'])

        for filestore, kwargs in COLLECTIONS.items():
            controller = FileStoreController(filestore)
            mapper.collection(controller=controller, **kwargs)

        super(Router, self).__init__(mapper)



