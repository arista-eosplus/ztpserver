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

log = logging.getLogger(__name__)   #pylint: disable=C0103

class FileObjectNotFound(Exception):
    """ raised if url not found in the file store """
    pass

class FileStoreError(Exception):
    """ base exception class for FileStore objects """
    pass

class FileObjectError(Exception):
    ''' base exception class for FileObject '''
    pass

class FileObject(object):
    """ represents a file object from the file store """

    def __init__(self, name, path=None):

        self.name = name
        if path is not None:
            self.name = os.path.join(path, name)

        self.type, self.encoding = mimetypes.guess_type(self.name)

    def __repr__(self):
        return "FileObject(name=%s)" % self.name

    @property
    def contents(self):
        contents = None
        if not os.access(self.name, os.R_OK):
            raise FileObjectError('could not access file %s' % self.name)
        if self.exists:
            contents = open(self.name).read()
        return contents

    @property
    def exists(self):
        return os.path.exists(self.name)


class FileStore(object):
    """ represents the file store """

    def __init__(self, path):
        """ creates a FileStore object at the specified root. """

        self.path = path

    def __repr__(self):
        return "FileStore(path=%s)" % self.path

    def _transform(self, filepath):
        """ combine the filepath with FileStore path """

        if not str(filepath).startswith(self.path):
            filepath = filepath[1:] if filepath[0] == '/' else filepath
            filepath = os.path.join(self.path, filepath)
        return filepath

    def add_folder(self, folderpath):
        folderpath = self._transform(folderpath)
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        return folderpath

    def write_file(self, filepath, contents, binary=False):
        try:
            mode = 'wb' if binary else 'w'
            filepath = self._transform(filepath)
            open(filepath, mode).write(contents)
        except:
            log.error('Unable to write file %s', filepath)
            raise

    def exists(self, filepath):
        filepath = self._transform(filepath)
        return os.path.exists(filepath)

    def get_file(self, filepath):
        filepath = self._transform(filepath)
        if not self.exists(filepath):
            raise FileObjectNotFound(filepath)
        return FileObject(filepath)

    def delete_file(self, filepath):
        filepath = self._transform(filepath)
        if os.path.exists(filepath):
            os.remove(filepath)


def create_file_store(name, basepath=None):
    """ creates a new FileStore object """

    if basepath is None:
        basepath = ztpserver.config.runtime.default.data_root

    log.debug('creating FileStore[%s] with basepath=%s', name, basepath)
    name = name[1:] if str(name).startswith('/') else name
    basepath = os.path.join(basepath, name)

    if not os.path.exists(basepath):
        log.debug('invalid basepath, not creating FileStore instance')
        raise FileStoreError('invalid path %s' % basepath)

    return FileStore(basepath)

















