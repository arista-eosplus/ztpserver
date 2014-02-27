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
import os

import routes
import webob

import ztpserver.config
import ztpserver.controller

class TestRouter(unittest.TestCase):

    def setUp(self):
        path = os.path.join(os.getcwd(), 'test/filestore')
        ztpserver.config.runtime.set_value('data_root', path, 'default')

    def test_router_object(self):
        rtr = ztpserver.controller.Router()
        self.assertIsInstance(rtr, ztpserver.controller.Router)

    def test_router_map(self):
        rtr = ztpserver.controller.Router()
        for url in ['/bootstrap', '/actions/test', '/objects/test',
            '/bootstrap/config']:
            obj = rtr.map.match(url)
            self.assertIsNotNone(obj)

    def test_router_req_get_bootstrap(self):
        rtr = ztpserver.controller.Router()

        headers = [
            ('X-Arista-Softwarereversion', '4.12.0'),
            ('X-Arista-Architecture', 'i386'),
            ('X-Arista-Modelname', 'vEOS'),
            ('X-Arista-Systemmac', '00:0c:29:f5:d2:7d'),
            ('X-Arista-Serialnumber', '1234567890')
        ]
        req = webob.Request.blank('/bootstrap', headers=headers)
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')

    def test_router_req_get_config(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/bootstrap/config')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_router_req_get_actions_with_id_valid(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/actions/test.py')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')

    def test_router_req_get_actions_with_id_invalid(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/actions/invalid.py')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 404)

    def test_router_req_post_actions_invalid(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/actions/test.py', method='POST')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 404)

    def test_router_req_get_objects_with_id_valid(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/objects/test.py')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'text/x-python')

    def test_router_req_get_objects_with_id_invalid(self):
        rtr = ztpserver.controller.Router()
        req = webob.Request.blank('/objects/invalid.py')
        resp = req.get_response(rtr)
        self.assertEqual(resp.status_code, 404)

class TestFileStoreController(unittest.TestCase):

    def test_file_store_controller_object(self):
        path = os.path.join(os.getcwd(), 'test/filestore')
        obj = ztpserver.controller.FileStoreController('actions', path_prefix=path)
        self.assertEqual(repr(obj), 'FileStoreController')

    def test_file_store_controller_get_actions_with_id(self):
        path = os.path.join(os.getcwd(), 'test/filestore')
        controller = ztpserver.controller.FileStoreController('actions', path_prefix=path)

        collection = ztpserver.controller.COLLECTIONS['actions']
        mapper = routes.Mapper()
        mapper.collection(**collection)
        kwargs = { 'urlvars': mapper.match('/actions/test.py') }

        req = webob.Request.blank('/actions/test/py', **kwargs)

        obj = controller.show(req, 'test.py')
        self.assertIsInstance(obj, webob.static.FileApp)






if __name__ == '__main__':
    unittest.main()
