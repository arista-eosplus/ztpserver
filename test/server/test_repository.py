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

from ztpserver.repository import FileObject, FileStore, FileObjectNotFound
from ztpserver.repository import create_file_store

from server_test_lib import create_filestore, FILESTORE
from server_test_lib import remove_all, random_string

class SuccessFileObjectTests(unittest.TestCase):

    def setUp(self):
        self.filestore = create_filestore()
        assert os.path.exists(FILESTORE)

    def tearDown(self):
        remove_all()

    def test_success(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(FILESTORE, filename)
        self.filestore.write_file(filename, contents)

        obj = FileObject(filename, path=FILESTORE)
        self.assertTrue(obj.name, filepath)
        self.assertTrue(obj.exists)
        self.assertEqual(obj.contents, contents)

    def test_file_missing(self):
        filename = random_string()
        obj = FileObject(filename, path=FILESTORE)
        self.assertFalse(obj.exists)
        self.assertIsNone(obj.contents)



class SuccessFileStoreTests(unittest.TestCase):

    def setUp(self):
        create_filestore()
        assert os.path.exists(FILESTORE)

        self.filestore = FileStore(FILESTORE)

    def tearDown(self):
        remove_all()

    def test_success(self):
        self.assertIsInstance(self.filestore, FileStore)
        self.assertEqual(repr(self.filestore), 'FileStore(path=%s)' % FILESTORE)
        self.assertEqual(self.filestore.path, FILESTORE)
        self.assertEqual(self.filestore._cache, dict())

    def test_add_folder(self):
        folder = random_string()
        self.filestore.add_folder(folder)
        self.assertTrue(os.path.join(FILESTORE, folder))

    def test_add_nested_folder(self):
        folder = '%s/%s/%s' % \
            (random_string(), random_string(), random_string())
        self.filestore.add_folder(folder)
        self.assertTrue(os.path.join(FILESTORE, folder))

    def test_write_file(self):
        filename = random_string()
        contents = random_string()
        self.filestore.write_file(filename, contents)
        filepath = os.path.join(FILESTORE, filename)
        self.assertTrue(filepath)
        self.assertEqual(open(filepath).read(), contents)

    def test_file_exists(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(FILESTORE, filename)
        open(filepath, 'w').write(contents)
        self.filestore.exists(filepath)

        self.filestore.write_file(filename, contents)
        filepath = os.path.join(FILESTORE, filename)
        self.assertTrue(filepath)
        self.assertEqual(open(filepath).read(), contents)

    def test_get_file(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(FILESTORE, filename)
        open(filepath, 'w').write(contents)
        obj = self.filestore.get_file(filename)
        self.assertIsInstance(obj, FileObject)
        self.assertTrue(obj.exists)

    def test_get_file_missing(self):
        filename = random_string()
        assert not os.path.exists(os.path.join(FILESTORE, filename))
        self.assertRaises(FileObjectNotFound,
                          self.filestore.get_file,
                          filename)

    def test_delete_file(self):
        filename = random_string()
        contents = random_string()
        filepath = os.path.join(FILESTORE, filename)
        open(filepath, 'w').write(contents)
        assert os.path.exists(filepath)
        self.filestore.delete_file(filepath)
        self.assertFalse(os.path.exists(filepath))

    def test_delete_file(self):
        filename = random_string()
        filepath = os.path.join(FILESTORE, filename)
        assert not os.path.exists(filepath)
        self.filestore.delete_file(filepath)
        self.assertFalse(os.path.exists(filepath))

    def test_create_file_store(self):
        fsname = random_string()
        filepath = os.path.join(FILESTORE, fsname)
        os.makedirs(filepath)

        obj = create_file_store(fsname, basepath=FILESTORE)
        self.assertIsInstance(obj, FileStore)
        self.assertTrue(os.path.exists(filepath))

if __name__ == '__main__':
    unittest.main()
