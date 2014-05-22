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
import warnings
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


class TextSerializer(object):

    def deserialize(self, data):
        ''' Deserialize a text object and return a dict '''
        return str(data)

    def serialize(self, data):
        ''' Serialize a dict object and return text '''
        return str(data)


class YAMLSerializer(object):

    def __new__(cls):
        if not YAML_AVAILABLE:
            warnings.warn('Unable to import YAML', RuntimeWarning)
            return None
        else:
            return super(YAMLSerializer, cls).__new__(cls)

    def deserialize(self, data):
        ''' Deserialize a YAML object and return a dict '''

        try:
            return yaml.safe_load(data)
        except yaml.YAMLError:
            log.exception('Unable to deserialize YAML data')
            raise

    def serialize(self, data, safe_dump=False):
        ''' Serialize a dict object and return YAML '''

        try:
            if safe_dump:
                return yaml.safe_dump(data, default_flow_style=False)
            return yaml.dump(data, default_flow_style=False)
        except yaml.YAMLError:
            log.exception('Unable to serialize YAML data')
            raise

class JSONSerializer(object):

    def deserialize(self, data):
        ''' Deserialize a JSON object and return a dict '''

        try:
            return json.loads(data)
        except:
            log.exception('Unable to deserialize JSON data')
            raise

    def serialize(self, data):
        ''' Serialize a dict object and return JSON '''

        try:
            return json.dumps(data)
        except:
            log.exception('Unable to serialize JSON data')
            raise


class Serializer(object):

    handlers = {
        'text/plain': TextSerializer(),
        'application/json': JSONSerializer(),
        'application/yaml': YAMLSerializer()
    }

    def serialize(self, obj, content_type=None, **kwargs):
        ''' Serialize the data based on the content_type '''

        try:
            handler = self.handlers.get(content_type, TextSerializer())
            return handler.serialize(obj, **kwargs)
        except:
            log.error('Unable to serialize data')
            raise SerializerError

    def deserialize(self, obj, content_type=None, cls=None, **kwargs):
        ''' Deserialize the data based on the content_type '''

        try:
            handler = self.handlers.get(content_type, TextSerializer())
            obj = self._convert(handler.deserialize(obj, **kwargs))
            if cls:
                obj = cls(**obj)
            return obj
        except:
            log.error('Unable to deserialize data')
            raise SerializerError

    @staticmethod
    def _convert(data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict([Serializers._convert(x) for x in data.items()])
        elif isinstance(data, collections.Iterable):
            return type(data)([Serializers._convert(x) for x in data])
        else:
            return data


def loads(obj, content_type=None, cls=None, **kwargs):
    try:
        serializer = Serializer()
        return serializer.deserialize(obj, content_type, cls=cls, **kwargs)
    except SerializerError as exc:
        log.error('Unable to deserialize object with content-type %s',
                  content_type)
        raise

def load(filepath, content_type=None, cls=None, **kwargs):
    try:
        contents = open(filepath).read()
        return loads(contents, content_type, cls=cls, **kwargs)
    except (OSError, IOError):
        log.error('Unable to load file from %s', filepath)
        raise

def dumps(obj, content_type=None, cls=None, **kwargs):
    try:
        serializer = Serializer()
        if hasattr(obj, 'serialize'):
            obj = obj.serialize()
        return serializers.serialize(obj, content_type, cls=cls, **kwargs)
    except SerializerError:
        log.error('Unable to serialize object with content-type %s',
                  content_type)
        raise

def dump(obj, filepath, content_type=None, cls=None, **kwargs):
    try:
        with open(filepath, 'w') as fh:
            fh.write(self.dumps(obj, content_type, cls=cls, **kwargs))
    except (OSError, IOError):
        log.error('Unable to write to file %s', filepath)
        raise


