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
#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=R0904,C0103
#
import unittest

from mock import patch

from ztpserver.serializers import SerializerError

from ztpserver.repository import FileObject, FileObjectError
from ztpserver.repository import Repository, RepositoryError
from ztpserver.repository import FileObjectNotFound

from server_test_lib import enable_logging, random_string

class FileObjectUnitTests(unittest.TestCase):

    @patch('ztpserver.serializers.load')
    def test_read_success(self, m_load):
        m_load.return_value = random_string()
        obj = FileObject(random_string())
        result = obj.read()
        self.assertEqual(m_load.return_value, result)

    @patch('ztpserver.serializers.load')
    def test_read_failure(self, m_load):
        m_load.side_effect = SerializerError
        obj = FileObject(random_string())
        self.assertRaises(FileObjectError, obj.read)

    @classmethod
    @patch('ztpserver.serializers.dump')
    def test_write_success(cls, _):
        obj = FileObjectError(random_string())
        obj = FileObject(random_string())
        obj.write(random_string())

    @patch('ztpserver.serializers.dump')
    def test_write_failure(self, m_dump):
        m_dump.side_effect = SerializerError
        obj = FileObject(random_string())
        self.assertRaises(FileObjectError, obj.write, random_string())


class RepositoryUnitTests(unittest.TestCase):

    @classmethod
    @patch('os.makedirs')
    def test_add_folder_success(cls, _):
        store = Repository(random_string())
        store.add_folder(random_string())

    @patch('os.makedirs')
    def test_add_folder_failure(self, m_makedirs):
        m_makedirs.side_effect = OSError
        store = Repository(random_string())
        self.assertRaises(RepositoryError, store.add_folder, random_string())

    @patch('ztpserver.repository.FileObject')
    @patch('os.chmod')
    def test_create_file_success(self, _, m_fileobj):
        store = Repository(random_string())
        store.add_file(random_string())
        self.assertFalse(m_fileobj.return_value.write.called)

    @patch('ztpserver.repository.FileObject')
    @patch('os.chmod')
    def test_create_file_with_contents_success(self, _,
                                               m_fileobj):
        store = Repository(random_string())
        store.add_file(random_string(), random_string())
        self.assertTrue(m_fileobj.return_value.write.called)
            
    @patch('ztpserver.repository.FileObject')
    def test_create_file_failure(self, m_fileobj):
        m_fileobj.return_value.write.side_effect = FileObjectError
        store = Repository(random_string())
        self.assertRaises(FileObjectError, store.add_file,
                          random_string(), random_string())

    @patch('os.path.exists')
    def test_exists_success(self, _):
        store = Repository(random_string())
        result = store.exists(random_string())
        self.assertTrue(result)

    @patch('os.path.exists')
    def test_exists_missing_file(self, m_exists):
        m_exists.return_value = False
        store = Repository(random_string())
        result = store.exists(random_string())
        self.assertFalse(result)

    @patch('os.path.exists')
    @patch('ztpserver.repository.FileObject')
    def test_get_file_success(self, m_fileobj, _):
        store = Repository(random_string())
        store.get_file(random_string())
        self.assertTrue(m_fileobj.called)

    @patch('os.path.exists')
    @patch('ztpserver.repository.FileObject')
    def test_get_file_failure(self, m_fileobj, m_exists):
        m_exists.return_value = False
        store = Repository(random_string())
        self.assertRaises(FileObjectNotFound, store.get_file, random_string())
        self.assertFalse(m_fileobj.called)

    @patch('os.remove')
    def test_delete_file_success(self, m_remove):
        store = Repository(random_string())
        store.delete_file(random_string())
        self.assertTrue(m_remove.called)

    @patch('os.remove')
    def test_delete_file_failure(self, m_remove):
        m_remove.side_effect = OSError
        store = Repository(random_string())
        self.assertRaises(RepositoryError, store.delete_file, random_string())


if __name__ == '__main__':
    enable_logging()
    unittest.main()
