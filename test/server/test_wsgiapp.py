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
import unittest

import routes
import webob

import ztpserver.wsgiapp

class TestRouter(unittest.TestCase):

    def setUp(self):
        self.mapper = routes.Mapper()

        self.mapper.collection('tests', 'test',
                                controller=ztpserver.wsgiapp.Controller())


    @webob.dec.wsgify
    def _index(self, request):
        return webob.Response(status=200)

    def test_router_index(self):
        self.mapper.connect('index', '/',
               controller=self._index,
               action='index')

        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.status, '200 OK')

    def test_router_wsgiapp_controller_index(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_create(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_new(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_show(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_update(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_delete(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')

    def test_router_wsgiapp_controller_edit(self):
        obj = ztpserver.wsgiapp.Router(self.mapper)
        req = webob.Request.blank('/tests', method='POST')
        resp = req.get_response(obj)

        self.assertIsInstance(resp, webob.Response)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.status, '204 No Content')


if __name__ == '__main__':
    unittest.main()



