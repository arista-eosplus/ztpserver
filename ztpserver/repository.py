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
#
import os
import mimetypes
import logging

import ztpserver.config
import ztpserver.serializers

log = logging.getLogger(__name__)   #pylint: disable=C0103

class FileObjectNotFound(Exception):
    """ raised if url not found in the file store """
    pass

class RepositoryError(Exception):
    """ base exception class for FileStore objects """
    pass

class FileObjectError(Exception):
    ''' base exception class for FileObject '''
    pass

class FileObject(object):

    def __init__(self, name, path=None, **kwargs):
        self.name = name
        if path is not None:
            self.name = os.path.join(path, name)

        self.type, self.encoding = mimetypes.guess_type(self.name)
        self.content_type = kwargs.get('content_type')

    def __repr__(self):
        return 'FileObject(name=%s)' % self.name

    def read(self, content_type=None, cls=None):
        try:
            return ztpserver.serializers.load(self.name, content_type, cls)
            self.content_type = content_type
        except ztpserver.serializers.SerializerError:
            log.error('Could not access file %s', self.name)
            raise FileObjectError

    def write(self, contents, content_type=None):
        try:
            ztpserver.serializers.dump(contents, self.name, content_type)
            self.content_type = content_type
        except ztpserver.serializers.SerializerError:
            log.error('Unable to write file %s', self.name)
            raise FileObjectError


class Repository(object):

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "Respository(path=%s)" % self.path

    def expand(self, filepath):
        if filepath == '/':
            filepath = self.path
        elif not str(filepath).startswith(self.path):
            filepath = filepath[1:] if filepath[0] == '/' else filepath
            filepath = os.path.join(self.path, filepath)
        return filepath

    def add_folder(self, folderpath):
        try:
            folderpath = self.expand(folderpath)
            os.makedirs(folderpath)
            return folderpath
        except OSError:
            log.error('Unable to add folder %s', folderpath)
            raise RepositoryError

    def create_file(self, filepath, contents=None, content_type=None):
        try:
            filepath = self.expand(filepath)
            obj = FileObject(filepath)
            if contents:
                obj.write(contents, content_type)
        except FileObjectError:
            raise RepositoryError

    def exists(self, filepath):
        filepath = self.expand(filepath)
        return os.path.exists(filepath)

    def get_file(self, filepath):
        filepath = self.expand(filepath)
        if not self.exists(filepath):
            raise FileObjectNotFound
        return FileObject(filepath)

    def delete_file(self, filepath):
        try:
            filepath = self.expand(filepath)
            os.remove(filepath)
        except (OSError, IOError):
            log.exception('Unable to delete file %s', filepath)
            raise RepositoryError




















