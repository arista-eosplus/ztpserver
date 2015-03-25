# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# Copyright (c) 2015, Arista Networks, Inc.
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

#pylint: disable=R0904,C0103

import unittest
import httplib
import routes

import webob

from ztpserver.wsgiapp import WSGIController, WSGIRouter

class TestWsgiApp(unittest.TestCase):

    def setUp(self):
        mapper = routes.Mapper()
        mapper.collection('tests', 'test', controller=WSGIController)

        self.router = WSGIRouter(mapper)

    def request(self, url, method='GET', **kwargs):
        req = webob.Request.blank(url, method=method, **kwargs)
        return req.get_response(self.router)

    def get_url(self, url, expected_status=httplib.OK, **kwargs):
        resp = self.request(url, **kwargs)
        self.assertEqual(resp.status_code, expected_status)
        return resp

    def post_url(self, url, expected_status=httplib.OK, **kwargs):
        resp = self.request(url, 'POST', **kwargs)
        self.assertEqual(resp.status_code, expected_status)
        return resp

    def put_url(self, url, expected_status=httplib.OK, **kwargs):
        resp = self.request(url, 'PUT', **kwargs)
        self.assertEqual(resp.status_code, expected_status)
        return resp

    def delete_url(self, url, expected_status=httplib.OK, **kwargs):
        resp = self.request(url, 'DELETE', **kwargs)
        self.assertEqual(resp.status_code, expected_status)
        return resp

    def test_get_url_collection(self):
        self.get_url('/tests', 204)

    def test_get_url_resource(self):
        self.get_url('/test/resource', 404)

    def test_get_url_missing(self):
        self.get_url('/missing', 404)

    def test_post_url_collection(self):
        self.post_url('/tests', 204)

    def test_post_url_resource(self):
        self.post_url('/test/resource', 404)

    def test_post_url_missing(self):
        self.post_url('/missing', 404)

    def test_put_url_collection(self):
        self.put_url('/tests', 404)

    def test_put_url_resource(self):
        self.put_url('/test/resource', 404)

    def test_put_url_missing(self):
        self.put_url('/missing', 404)

    def test_delete_url_collection(self):
        self.delete_url('/tests', 404)

    def test_delete_url_resource(self):
        self.delete_url('/test/resource', 404)

    def test_delete_url_missing(self):
        self.delete_url('/missing', 404)

if __name__ == '__main__':
    unittest.main()



