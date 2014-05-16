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
# pylint: disable=R0904,C0103
#
import unittest
import os

import ztpserver.repository

from ztpserver.repository import FileObject, FileStore
from ztpserver.repository import FileObjectNotFound, FileObjectError
from ztpserver.repository import create_filestore

from server_test_lib import random_string, remove_all
from server_test_lib import add_folder, write_file

class FileObjectUnitTests(unittest.TestCase):

    def tearDown(self):
        remove_all()

    def test_success(self):
        filename = random_string()
        contents = random_string()

        filepath = write_file(contents, filename)
        path = os.path.dirname(filepath)
        assert os.path.exists(filepath)

        obj = FileObject(filename, path=path)

        self.assertTrue(obj.name, filepath)
        self.assertTrue(obj.exists)
        self.assertEqual(obj.contents, contents)

    def test_file_missing(self):
        filename = random_string()
        obj = FileObject(filename)

        def contents(obj):
            return obj.contents

        self.assertRaises(ztpserver.repository.FileObjectError, contents, obj)
        self.assertFalse(obj.exists)

class FileStoreUnitTests(unittest.TestCase):

    def setUp(self):
        self.filepath = add_folder('filestore')
        assert os.path.exists(self.filepath)

        self.filestore = FileStore(self.filepath)

    def tearDown(self):
        remove_all()

    def test_success(self):
        self.assertIsInstance(self.filestore, FileStore)
        self.assertEqual(repr(self.filestore), 'FileStore(path=%s)' % \
            self.filepath)

    def test_add_folder(self):
        folder = random_string()
        self.filestore.add_folder(folder)

        filepath = os.path.join(self.filepath, folder)
        self.assertTrue(os.path.exists(filepath))

    def test_add_nested_folder(self):
        folder = '%s/%s/%s' % \
            (random_string(), random_string(), random_string())
        self.filestore.add_folder(folder)

        filepath = os.path.join(self.filepath, folder)
        self.assertTrue(os.path.exists(filepath))

    def test_write_file(self):
        filename = random_string()
        contents = random_string()
        self.filestore.write_file(filename, contents)

        filepath = os.path.join(self.filepath, filename)
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(open(filepath).read(), contents)

    def test_file_exists(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(self.filepath, filename)
        write_file(contents, filepath)
        assert os.path.exists(filepath)

        self.assertTrue(self.filestore.exists(filename))

    def test_file_exists_failure(self):
        filename = random_string()
        assert not os.path.exists(os.path.join(self.filepath, filename))

        self.assertFalse(self.filestore.exists(filename))

    def test_get_file(self):

        filename = random_string()
        contents = random_string()
        filepath = os.path.join(self.filepath, filename)
        write_file(contents, filename=filepath)

        obj = self.filestore.get_file(filename)
        self.assertIsInstance(obj, ztpserver.repository.FileObject)
        self.assertTrue(obj.exists)
        self.assertEqual(filepath, obj.name)

    def test_get_file_missing(self):
        filename = random_string()
        assert not os.path.exists(os.path.join(self.filepath, filename))

        self.assertRaises(ztpserver.repository.FileObjectNotFound,
                          self.filestore.get_file,
                          filename)

    def test_delete_file(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(self.filepath, filename)
        write_file(contents, filepath)
        assert os.path.exists(filepath)

        self.filestore.delete_file(filename)
        self.assertFalse(os.path.exists(filename))

    def test_delete_missing_file(self):
        filename = random_string()
        filepath = os.path.join(self.filepath, filename)
        assert not os.path.exists(filepath)

        self.filestore.delete_file(filepath)
        self.assertFalse(os.path.exists(filepath))

    def test_create_filestore(self):
        fsname = random_string()
        filepath = os.path.join(self.filepath, fsname)
        os.makedirs(filepath)
        assert os.path.exists(filepath)

        obj = create_filestore(fsname, basepath=self.filepath)
        self.assertIsInstance(obj, ztpserver.repository.FileStore)
        self.assertTrue(os.path.exists(filepath))

if __name__ == '__main__':
    unittest.main()
