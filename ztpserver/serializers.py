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
import collections
import logging
import json

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


log = logging.getLogger(__name__)   #pylint: disable=C0103


class SerializerError(Exception):
    ''' base error raised by serialization functions '''
    pass


class BaseSerializer(object):
    ''' Base serializer object '''

    def serialize(self, data, **kwargs):
        ''' Serialize a dict to object '''
        raise NotImplementedError

    def deserialize(self, data, **kwargs):
        ''' Deserialize an object to dict '''
        raise NotImplementedError


class TextSerializer(BaseSerializer):

    def deserialize(self, data, **kwargs):
        ''' Deserialize a text object and return a dict '''
        return str(data)

    def serialize(self, data, **kwargs):
        ''' Serialize a dict object and return text '''
        return str(data)


class YAMLSerializer(BaseSerializer):

    def __new__(cls):
        if not YAML_AVAILABLE:
            log.error('Unable to import YAML')
            return None
        else:
            return super(YAMLSerializer, cls).__new__(cls)

    def deserialize(self, data, **kwargs):
        ''' Deserialize a YAML object and return a dict '''

        try:
            return yaml.safe_load(data)
        except yaml.YAMLError as err:
            log.error('Unable to deserialize YAML data %s (%s)' % 
                      (data, err))
            raise

    def serialize(self, data, safe_dump=False, **kwargs):
        ''' Serialize a dict object and return YAML '''

        try:
            if safe_dump:
                return yaml.safe_dump(data, default_flow_style=False)
            return yaml.dump(data, default_flow_style=False)
        except yaml.YAMLError as err:
            log.error('Unable to serialize YAML data %s (%s)' % 
                      (data, err))
            raise


class JSONSerializer(BaseSerializer):

    def deserialize(self, data, **kwargs):
        ''' Deserialize a JSON object and return a dict '''

        try:
            return json.loads(data)
        except Exception as err:
            log.error('Unable to deserialize JSON data %s (%s)' %
                      (data, err))
            raise

    def serialize(self, data, **kwargs):
        ''' Serialize a dict object and return JSON '''

        try:
            return json.dumps(data)
        except Exception as err:
            log.error('Unable to deserialize JSON data %s (%s)' %
                      (data, err))
            raise


class Serializer(object):

    def __init__(self):
        self._handlers = {
            'text/plain': TextSerializer(),
            'application/json': JSONSerializer(),
            'application/yaml': YAMLSerializer()
        }

    @property
    def handlers(self):
        return self._handlers

    def add_handler(self, content_type, instance):
        if content_type in self._handlers:
            log.warning('Overwriting previous loaded handler %s', content_type)
        self._handlers[content_type] = instance

    def serialize(self, obj, content_type=None, **kwargs):
        ''' Serialize the data based on the content_type '''

        try:
            handler = self.handlers.get(content_type, TextSerializer())
            return handler.serialize(obj, **kwargs)
        except Exception as err:
            log.error('Unable to serialize obj:%s, content_type:%s (%s)' %
                      (obj, content_type, err))
            raise SerializerError('Unable to serialize obj:%s, content_type:%s '
                                  '(%s)' % (obj, content_type, err))
        
    def deserialize(self, obj, content_type=None, cls=None, **kwargs):
        ''' Deserialize the data based on the content_type '''

        try:
            handler = self.handlers.get(content_type, TextSerializer())
            obj = self._convert_from_unicode(handler.deserialize(obj, **kwargs))
            if cls:
                obj = cls(**obj)    #pylint: disable=W0142
            return obj
        except Exception as err:
            log.error('Unable to deserailize obj:%s, content_type:%s, cls:%s '
                      '(%s)' % (obj, content_type, cls, err))
            raise SerializerError('Unable to deserailize obj:%s, '
                                  'content_type:%s, cls:%s (%s)' % 
                                  (obj, content_type, cls, err))

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


def loads(obj, content_type=None, cls=None, **kwargs):
    serializer = Serializer()
    return serializer.deserialize(obj, content_type, cls=cls, **kwargs)

def load(file_path, content_type=None, cls=None, **kwargs):
    try:
        contents = open(file_path).read()
        return loads(contents, content_type, cls=cls, **kwargs)
    except (OSError, IOError) as err:
        log.error('Failed to load file from %s (%s)' % 
                  (file_path, err))
        raise SerializerError('Failed to load file from %s (%s)' % 
                              (file_path, err))

def dumps(obj, content_type=None, cls=None, **kwargs):
    serializer = Serializer()
    if hasattr(obj, 'serialize'):
        obj = obj.serialize()
    return serializer.serialize(obj, content_type, cls=cls, **kwargs)

def dump(obj, file_path, content_type=None, cls=None, **kwargs):
    try:
        with open(file_path, 'w') as fhandler:
            fhandler.write(dumps(obj, content_type, cls=cls, **kwargs))
    except (OSError, IOError) as err:
        log.error('Failed to write file to %s (%s)' % 
                  (file_path, err))
        raise
