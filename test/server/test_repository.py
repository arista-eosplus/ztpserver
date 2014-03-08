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

import ztpserver.repository

class TestNode(unittest.TestCase):

    def test_create_node(self):
        headers = {
            'X-Arista-Softwarereversion': '4.12.0',
            'X-Arista-Architecture': 'i386',
            'X-Arista-Modelname': 'vEOS',
            'X-Arista-Systemmac': '00:0c:29:f5:d2:7d',
            'X-Arista-Serialnumber': '1234567890'
        }

        obj = ztpserver.repository.create_node(headers)
        self.assertEqual(obj.softwarereversion, '4.12.0')
        self.assertEqual(obj.architecture, 'i386')
        self.assertEqual(obj.modelname, 'vEOS')
        self.assertEqual(obj.systemmac, '00:0c:29:f5:d2:7d')
        self.assertEqual(obj.serialnumber, '1234567890')




class TestFileObject(unittest.TestCase):

    def test_create_file_object_with_path(self):
        path = os.path.join(os.getcwd(), 'test')
        fn = 'test_repository.py'
        obj = ztpserver.repository.FileObject(fn, path)

        self.assertEqual(repr(obj), 'FileObject(name=%s, type=%s)' %
            (os.path.join(path, fn), 'text/x-python'))

    def test_create_file_object_without_path(self):
        path = os.path.join(os.getcwd(), 'test', 'test_repository.py')
        obj = ztpserver.repository.FileObject(path)
        self.assertEqual(repr(obj), 'FileObject(name=%s, type=%s)' %
            (path, 'text/x-python'))

    def test_get_file_contents_valid_file(self):
        path = os.path.join(os.getcwd(), 'test/server')
        fn = 'test_repository.py'
        obj = ztpserver.repository.FileObject(fn, path)
        fh = open(os.path.join(path, fn)).read()
        self.assertEqual(obj.contents, fh)

    def test_get_file_contents_invalid_file(self):
        obj = ztpserver.repository.FileObject('this_is_an_invalid_file')
        self.assertIsNone(obj.contents)

class TestFileStore(unittest.TestCase):

    def test_create_file_store(self):
        name = 'test'
        path = os.path.join(os.getcwd(), name)

        obj = ztpserver.repository.create_file_store(name, os.getcwd())
        self.assertEqual(repr(obj), "FileStore(path=%s)" % path)

    def test_get_file_valid(self):
        filestore = 'test/server'
        filename = 'test_repository.py'
        path = os.path.join(os.getcwd(), filestore, filename)
        fspath = os.path.join(os.getcwd(), filestore)

        obj = ztpserver.repository.create_file_store(filestore, basepath=os.getcwd())
        fobj = obj.get_file(filename)
        self.assertEqual(repr(fobj), 'FileObject(name=%s, type=%s)' %
            (path, 'text/x-python'))

    def test_get_file_invalid(self):
        obj = ztpserver.repository.create_file_store('test', os.getcwd())
        self.assertRaises(ztpserver.repository.FileObjectNotFound,
                          obj.get_file,
                          'invalid_filename')

if __name__ == '__main__':
    unittest.main()
