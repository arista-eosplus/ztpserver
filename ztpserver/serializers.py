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
# pylint: disable=R0201
#

from ztpserver.constants import CONTENT_TYPE_OTHER
from ztpserver.constants import CONTENT_TYPE_JSON
from ztpserver.constants import CONTENT_TYPE_YAML

import collections
import logging
import json
import os
import threading
import yaml

READ_WRITE_LOCK = {}
log = logging.getLogger(__name__)   #pylint: disable=C0103

class SerializerError(Exception):
    ''' base error raised by serialization functions '''
    pass


class BaseSerializer(object):
    ''' Base serializer object '''

    def __init__(self, node_id):
        self.node_id = node_id

    def serialize(self, data):
        ''' Serialize a dict to object '''
        raise NotImplementedError

    def deserialize(self, data):
        ''' Deserialize an object to dict '''
        raise NotImplementedError


class TextSerializer(BaseSerializer):

    def deserialize(self, data):
        ''' Deserialize a text object and return a dict '''
        return str(data)

    def serialize(self, data):
        ''' Serialize a dict object and return text '''
        return str(data)


class YAMLSerializer(BaseSerializer):

    def deserialize(self, data):
        ''' Deserialize a YAML object and return a dict '''

        try:
            return yaml.safe_load(data)
        except yaml.YAMLError as err:
            msg = '''%s: unable to deserialize YAML data:
%s 

Error:
%s''' % (self.node_id, data, err)
            raise SerializerError(msg)

    def serialize(self, data):
        ''' Serialize a dict object and return YAML '''

        try:
            return yaml.dump(data, default_flow_style=False)
        except yaml.YAMLError as err:
            msg = '''%s: unable to serialize YAML data:
%s 

Error:
%s''' % (self.node_id, data, err)
            raise SerializerError(msg)


class JSONSerializer(BaseSerializer):

    def deserialize(self, data):
        ''' Deserialize a JSON object and return a dict '''

        try:
            return json.loads(data)
        except Exception as err:
            msg = '''%s: unable to deserialize JSON data:
%s 

Error:
%s''' % (self.node_id, data, err)
            raise SerializerError(msg)

    def serialize(self, data):
        ''' Serialize a dict object and return JSON '''

        try:
            return json.dumps(data)
        except Exception as err:
            msg = '''%s: unable to serialize JSON data:
%s 

Error:
%s''' % (self.node_id, data, err)
            raise SerializerError(msg)


class Serializer(object):

    def __init__(self, node_id):
        self.node_id = node_id

        self._handlers = {
            CONTENT_TYPE_OTHER: TextSerializer(self.node_id),
            CONTENT_TYPE_JSON: JSONSerializer(self.node_id),
            CONTENT_TYPE_YAML: YAMLSerializer(self.node_id)
        }

    @property
    def handlers(self):
        return self._handlers

    def add_handler(self, content_type, instance):
        if content_type in self._handlers:
            log.warning('%s: overwriting previous loaded handler %s', 
                        (self.node_id, content_type))
        self._handlers[content_type] = instance

    def serialize(self, data, content_type):
        ''' Serialize the data based on the content_type '''

        handler = self.handlers.get(content_type, 
                                    TextSerializer(self.node_id))
        return handler.serialize(data)

    def deserialize(self, data, content_type=None):
        ''' Deserialize the data based on the content_type '''

        handler = self.handlers.get(content_type, 
                                    TextSerializer(self.node_id))
        data = self._convert_from_unicode(handler.deserialize(data))
        return data

    @staticmethod
    def _convert_from_unicode(data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict([Serializer._convert_from_unicode(x)
                         for x in data.items()])
        elif isinstance(data, collections.Iterable):
            return type(data)([Serializer._convert_from_unicode(x)
                               for x in data])
        else:
            return data


def loads(data, content_type, node_id):
    serializer = Serializer(node_id)
    return serializer.deserialize(data, content_type)

def load(file_path, content_type, node_id='N/A', lock=False):
    log.debug('%s: reading %s...' % (node_id, file_path))

    if lock and file_path not in READ_WRITE_LOCK:
        READ_WRITE_LOCK[file_path] = threading.Lock()

    try:
        if lock:
            with READ_WRITE_LOCK[file_path]:
                with open(file_path) as fhandler:
                    data = fhandler.read()
        else:
            with open(file_path) as fhandler:
                data = fhandler.read()            

        result = loads(data, content_type, node_id)
    except (OSError, IOError) as err:
        log.error('%s: failed to load file from %s (%s)' % 
                  (node_id, file_path, err))
        raise SerializerError('%s: failed to load file from %s (%s)' % 
                              (node_id, file_path, err))

    # Enable this log if you want to see the contents of the file (verbose)
    # log.debug('%s: loaded %s: %s' % (node_id, file_path, result))
    return result

def dumps(data, content_type, node_id):
    serializer = Serializer(node_id)
    if hasattr(data, 'serialize'):
        data = data.serialize()
    return serializer.serialize(data, content_type)


def dump(data, file_path, content_type, node_id='N/A', lock=False):
    log.debug('%s: writing %s...' % (node_id, file_path))

    if lock and file_path not in READ_WRITE_LOCK:
        READ_WRITE_LOCK[file_path] = threading.Lock()

    try:
        if lock:
            with READ_WRITE_LOCK[file_path]:
                with os.fdopen(os.open(file_path, 
                                       os.O_WRONLY | os.O_CREAT, 0754), 
                               'w') as fhandler:
                    fhandler.write(dumps(data, content_type, node_id))
        else:
            with os.fdopen(os.open(file_path, 
                                   os.O_WRONLY | os.O_CREAT, 0754), 
                           'w') as fhandler:
                fhandler.write(dumps(data, content_type, node_id))            
    except (OSError, IOError) as err:
        log.error('%s: failed to write file to %s (%s)' % 
                  (node_id, file_path, err))
        raise SerializerError('%s: failed to write file to %s (%s)' % 
                              (node_id, file_path, err))

    # Enable this log if you want to see the contents of the file (verbose)
    # log.debug('%s: wrote %s: %s' % (node_id, file_path, data))
