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
#
'''
    MODULE:
        ztpserver.respository

    AUTHOR:
        Arista Networks

    DESCRIPTION:
        The repository module provides read and write access to files
        for ztpserver.  The repository module can perform basic file
        system like functionality for performing basid CRUD on
        files and well as reading and writing specific file contents.

    :copyright: Copyright (c) 2015, Arista Networks
    :license: BSD, see LICENSE for more details

'''

import hashlib
import logging
import mimetypes
import os

import ztpserver.serializers

from ztpserver.serializers import SerializerError

log = logging.getLogger(__name__)   #pylint: disable=C0103



def create_repository(path):
    if not os.path.exists(path):
        raise RepositoryError('%s not found' % path)
    return Repository(path)


class RepositoryError(Exception):
    ''' Base exception class for :py:class:`Repository` '''
    pass

class FileObjectError(Exception):
    ''' Base exception class for :py:class:`FileObject` '''
    pass

class FileObjectNotFound(RepositoryError):
    ''' Raised when a requested file is not found in the repository.  This
    exception is a subclass of :py:class:`RespositoryError`
    '''
    pass



class FileObject(object):
    ''' The :py:class:`FileObject` represents a single file entity in the
    repository.   The instance provides convienent methods to read and write
    contents to the file using a specified serialization
    '''

    def __init__(self, name, path=None, **kwargs):
        ''' The initialize method for :py:class:`FileObject`

        :param name: the name of the file
        :type name: str
        :param path: the base path of the file
        :type path: str
        :param content_type: the content type of the file (optional)
        :type content_type: str
        :returns: object

        '''
        self.name = name
        if path is not None:
            self.name = os.path.join(path, name)

        self.type, self.encoding = mimetypes.guess_type(self.name)
        self.content_type = kwargs.get('content_type')

    def __repr__(self):
        return 'FileObject(name=%s, type=%s, encoding=%s, content_type=%s)' % \
               (self.name, self.type, self.encoding, self.content_type)

    def read(self, content_type=None, node_id=None):
        ''' Reads the contents from the file system

        :param content_type: defines the content_type of the file used to
                             deserialize the object
        :type content_type: str
        :returns: object
        :raises: FileObjectError

        The read method will read the file from the file system, deserializing
        the contents as specified by the content_type argument.  If the
        content_type argument is not specified, the read method will read
        the file as text. If any errors occur, a FileObjectError is raised.

        '''
        try:
            self.content_type = content_type
            return ztpserver.serializers.load(self.name, content_type,
                                              node_id)
        except SerializerError as err:
            raise FileObjectError(err.message)

    def write(self, contents, content_type=None):
        ''' Writes the contents to the file

        :param contents: specifies the contents to be written to the file
        :type contents: str
        :param content_type: defines the serialization format to use when
                             saving the file
        :type content_type: str
        :returns: None
        :raises: FileObjectError

        The write method takes the contents argument and writes it to the file
        using the serialization specified in the content_type argument.  If
        the content_type argument is not specified, the contents are written
        as string text.  This method will overwrite any contents that
        previously existed for the FileObj instance.  If any errors are
        encountered during the write operation, a FileObjectError is raised

        '''
        try:
            ztpserver.serializers.dump(contents, self.name, content_type)
            self.content_type = content_type
        except SerializerError as err:
            raise FileObjectError(err.message)

    def size(self):
        ''' Returns the size of the object in bytes.

        :raises: IOError
        '''
        return os.path.getsize(self.name)

    def hash(self):
        ''' Returns the SHA1 hash of the object.

        :raises: IOError
        '''

        sha1 = hashlib.sha1()
        sha1.update(open(self.name).read())       #pylint: disable=E1101
        return sha1.hexdigest()

class Repository(object):
    ''' The Respository class represents a repository of :py:class:`FileObject`
    instances.  It is an abstract wrapper providing the ability to interact
    with persistently stored files.
    '''

    def __init__(self, path):
        ''' The initialize method for :py:class:`Repository`

        :param path: the base path of the repository
        :type path: str
        :returns: object

        '''
        self.path = path

    def __repr__(self):
        return "Repository(path=%s)" % self.path

    def expand(self, file_path):
        ''' Expands a file_path to the full path to a file object

        :param file_path: the file path to expand
        :type file_path: str
        :returns: str -- the full path to the file

        This method is used to transform a relative file path into an
        absolute file path for identifying a file object resource

        '''
        if file_path == '/':
            file_path = self.path
        elif not str(file_path).startswith(self.path):
            file_path = file_path[1:] if file_path[0] == '/' else file_path
            file_path = os.path.join(self.path, file_path)
        return file_path

    def add_folder(self, folder_path):
        ''' Add a new folder to the repository

        :param folder_path: the full path of the folder to add
        :type folder_path: str
        :returns: str -- the full path to the new folder
        :raises: RespositoryError

        '''
        try:
            folder_path = self.expand(folder_path)
            os.makedirs(folder_path, 0774)
            return folder_path
        except OSError as err:
            log.error('Failed to add folder %s (%s)' %
                      (folder_path, err))
            raise RepositoryError('Failed to add folder %s (%s)' %
                                  (folder_path, err))

    def add_file(self, file_path, contents=None, content_type=None):
        ''' Adds a new :py:class:`FileObject` to the repository

        :param file_path: the full path of the file to add
        :type file_path: str
        :param contents: the contents to write to the file
        :type contents: str
        :param content_type: specifies the serialization to use for the file
        :type content_type: str
        :returns: :py:class:`FileObject`
        :raises: RespositoryError

        The add_file method allows for a new file to be added to the
        respository.  If the file already exists, it is returned as an instance
        of :py:class:`FileObject`.   If the file doesn't already exist and
        the contents argument is not None, then the file is created and
        the contents written to the file.  The content_type argument provides
        the serialization to be used when saving the file.

        '''
        file_path = self.expand(file_path)
        obj = FileObject(file_path)
        if contents:
            obj.write(contents, content_type)
        return obj

    def exists(self, file_path):
        ''' Returns boolean if the file_path exists in the repository

        :param file_path: the file_path to check for existence
        :type file_path: str
        :returns: boolean -- True if it exists otherwise False

        '''
        file_path = self.expand(file_path)
        return os.path.exists(file_path)

    def get_file(self, file_path):
        ''' Returns an intance of :py:class:`FileObject` if it exists

        :param file_path: the file path of the instance to return
        :type file_path: str
        :returns: instance of :py:class:`FileObject`
        :raises: FileObjectNotFound

        This method will retrieve a file object instance if it exists in the
        repository.  If the file does not exist then an error is raised

        '''
        file_path = self.expand(file_path)
        if not self.exists(file_path):
            raise FileObjectNotFound('file not found (%s)' % file_path)
        return FileObject(file_path)

    def delete_file(self, file_path):
        ''' Deletes an existing file in the respository

        :param file_path: the file path of the instance to delete
        :type file_path: str
        :returns: None
        :raises: RepositoryError

        '''
        try:
            file_path = self.expand(file_path)
            os.remove(file_path)
        except (OSError, IOError) as err:
            log.error('Failed to delete file %s (%s)' %
                      (file_path, err))
            raise RepositoryError('Failed to delete file %s (%s)' %
                                  (file_path, err))
