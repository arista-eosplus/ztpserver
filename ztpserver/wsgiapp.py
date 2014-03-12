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

import webob
import webob.dec
import webob.exc

import routes
import routes.middleware

from ztpserver.serializers import Serializer

log = logging.getLogger(__name__)

class Controller(object):

    def index(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def create(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def new(self, request, **kwargs):
        return webob.exc.HTTPNoContent()

    def show(self, request, id, **kwargs):
        return webob.exc.HTTPNoContent()

    def update(self, request, id, **kwargs):
        return webob.exc.HTTPNoContent()

    def delete(self, request, id, **kwargs):
        return webob.exc.HTTPNoContent()

    def edit(self, request, id, **kwargs):
        return webob.exc.HTTPNoContent()

    @webob.dec.wsgify
    def __call__(self, request):
        action = request.urlvars['action']
        content_type = request.content_type
        serializer = Serializer()

        try:
            method = getattr(self, action)
            result = method(request, **request.urlvars)

        except Exception as e:
            log.exception(e)
            raise webob.exc.HTTPInternalServerError()

        if isinstance(result, dict) or result is None:
            if not result:
                response = webob.exc.HTTPNoContent()

            else:
                status = 200
                content_type = content_type
                body = serializer.serialize(result, content_type)
                response = webob.Response(status=status,
                                          body=body,
                                          content_type=content_type)
            return response
        else:
            return result


class Router(object):

    def __init__(self, mapper):
        self.map = mapper
        self.router = routes.middleware.RoutesMiddleware(self.dispatch,
                                                         self.map)

    @webob.dec.wsgify
    def __call__(self, request):
        return self.router

    @webob.dec.wsgify
    def dispatch(self, request):
        try:
            return request.urlvars['controller']
        except KeyError:
            return webob.exc.HTTPNotFound()



