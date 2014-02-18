# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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
import os
import mimetypes
import collections
import logging

import ztpserver.config

log = logging.getLogger(__name__)


def create_node(headers):
    """ returns a Node object using HTTP X-Arista headers """

    kwargs = dict()
    for k,v in headers.items():
        if str(k).startswith('X-Arista'):
            key = str(k).replace('X-Arista-', '').lower()
            kwargs[key] = v
    Node = collections.namedtuple('Node', kwargs.keys())
    return Node(**kwargs)

class FileObjectNotFound(Exception):
    """ raised if url not found in the file store """
    pass

class FileStoreError(Exception):
    """ base exception class for FileStore objects """
    pass

class FileObject(object):
    """ represents a file object from the file store """

    def __init__(self, name, path=None):

        self.name = name
        if path is not None:
            self.name = os.path.join(path, name)

        self.type, self.encoding = mimetypes.guess_type(self.name)

    def __repr__(self):
        return "FileObject(name=%s, type=%s)" % (self.name, self.type)


class FileStore(object):
    """ represents the file store """

    def __init__(self, path):
        """ creates a FileStore object at the specified root. """

        self.path = path
        self._cache = dict()

    def __repr__(self):
        return "FileStore(path=%s)" % self.path

    def _transform(self, filepath):
        """ combine the filepath with FileStore path """

        if not str(filepath).startswith(self.path):
            filepath = filepath[1:] if filepath[0] == '/' else filepath
            filepath = os.path.join(self.path, filepath)
        return filepath

    def add_file(self, filepath):
        raise NotImplementedError

    def exists(self, filepath):
        filepath = self._transform(filepath)
        return os.path.exists(filepath)

    def get_file(self, filepath):
        filepath = self._transform(filepath)

        if not self.exists(filepath):
            raise FileObjectNotFound(filepath)

        if filepath in self._cache:
            return self._cache[filepath]

        obj = FileObject(filepath)
        self._cache[filepath] = obj

        return obj

    def delete_file(self, filepath):
        raise NotImplementedError


def create_file_store(name, basepath=None):
    """ creates a new FileStore object """

    if basepath is None:
        basepath = ztpserver.config.runtime.default.data_root

    name = name[1:] if str(name[0]).startswith('/') else name
    basepath = os.path.join(basepath, name)
    log.debug("create_file_store: basepath is %s" % basepath)

    if not os.path.exists(basepath):
        log.debug('invalid basepath, not creating FileStore instance')
        raise FileStoreError('invalid path %s' % basepath)

    log.debug('creating FileStore[%s] with basepath=%s' % (name, basepath))
    return FileStore(basepath)
















