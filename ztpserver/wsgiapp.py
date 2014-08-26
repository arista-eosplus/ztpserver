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
# pylint: disable=W0613,C0103,R0201,W0622,W0614
#
import logging

import webob
import webob.dec
import webob.exc

from routes.middleware import RoutesMiddleware

from ztpserver.serializers import dumps
from ztpserver.constants import CONTENT_TYPE_HTML, HTTP_STATUS_OK

log = logging.getLogger(__name__)

class WSGIController(object):

    def index(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def create(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def new(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def show(self, request, resource, **kwargs):
        return webob.exc.HTTPNotFound()

    def update(self, request, resource, **kwargs):
        return webob.exc.HTTPNotFound()

    def delete(self, request, resource, **kwargs):
        return webob.exc.HTTPNotFound()

    def edit(self, request, resource, **kwargs):
        return webob.exc.HTTPNotFound()

    def response(self, **kwargs):
        return webob.Response(**kwargs)

    @webob.dec.wsgify
    def __call__(self, request):
        action = request.urlvars['action']

        try:
            method = getattr(self, action)    #pylint: disable=R0921
            result = method(request, **request.urlvars)
        except Exception as exc:
            log.error('Unrecoverable error detected: %s' % exc.message)
            raise webob.exc.HTTPInternalServerError()

        if result is None:
            result = webob.exc.HTTPNoContent()

        elif isinstance(result, dict):
            # serialize body based on response content type
            if 'body' in result:
                content_type = result.get('content_type')
                result['body'] = dumps(result['body'], content_type,
                                       'general')

            result.setdefault('status', HTTP_STATUS_OK)
            result.setdefault('content_type', CONTENT_TYPE_HTML)

            result = self.response(**result)   #pylint: disable=W0142

        elif not isinstance(result, webob.Response) and \
             not isinstance(result, webob.static.FileApp):
            result = webob.exc.HTTPInternalServerError()

        return result

class WSGIRouter(object):

    def __init__(self, mapper):
        self.map = mapper
        self.router = RoutesMiddleware(self.route, self.map)

    @webob.dec.wsgify
    def __call__(self, request):
        return self.router

    @webob.dec.wsgify
    def route(self, request):
        ''' Routes the incoming request to the appropriate controller '''

        if 'controller' not in request.urlvars:
            log.debug('WSGIRouter: missing controller (request=%s)' % 
                      request)
            return webob.exc.HTTPNotFound()            

        controller = request.urlvars['controller']
        return controller()
