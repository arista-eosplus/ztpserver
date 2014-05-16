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
import json
import logging

from ztpserver.constants import CONTENT_TYPE_OTHER

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

log = logging.getLogger(__name__)   #pylint: disable=C0103

class SerializerError(Exception):
    ''' base error raised by serialization functions '''
    pass

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
        except:
            log.error('Unable to deserialize YAML data')
            raise

    def serialize(self, data, safe_dump=False):
        ''' Serialize a dict object and return YAML '''

        try:
            if safe_dump:
                return yaml.safe_dump(data, default_flow_style=False)
            return yaml.dump(data, default_flow_style=False)
        except:
            log.error('Unable to serialize YAML data')
            raise

class JSONSerializer(object):

    def deserialize(self, data):
        ''' Deserialize a JSON object and return a dict '''

        try:
            return json.loads(data)
        except:
            log.error('Unable to deserialize JSON data')
            raise

    def serialize(self, data):
        ''' Serialize a dict object and return JSON '''

        try:
            return json.dumps(data)
        except:
            log.error('Unable to serialize JSON data')
            raise

class Serializer(object):
    ''' The :py:class:`Serializer` will serialize a data structure
    based on the content-type.   If the content-type is not supported
    the :py:class:`Serializer` will simply return the data as a
    :py:class:`str` object
    '''

    def serialize(self, data, content_type, **kwargs):
        ''' Serialize the data based on the content_type '''

        #pylint: disable=E1103
        try:
            data = self.convert(data)
            handler = self._serialize_handler(content_type)
            return handler.serialize(data, **kwargs) if handler else str(data)
        except Exception as exc:
            log.exception(exc)
            raise SerializerError('Could not serialize data %s:' % data)

    def deserialize(self, data, content_type, **kwargs):
        ''' Deserialize the data based on the content_type '''

        try:
            handler = self._deserialize_handler(content_type)
            data = handler.deserialize(data, **kwargs) if handler else str(data)
            data = self.convert(data)
            return data
        except Exception as exc:
            log.exception(exc)
            raise SerializerError('Could not deserialize data: %s' % data)


    def _deserialize_handler(self, content_type):
        handlers = {
            'application/json': JSONSerializer(),
            'application/yaml': YAMLSerializer()
        }
        return handlers.get(content_type)


    def _serialize_handler(self, content_type):
        handlers = {
            'application/json': JSONSerializer(),
            'application/yaml': YAMLSerializer()
        }
        return handlers.get(content_type)

    @staticmethod
    def convert(data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict([Serializer.convert(x) for x in data.iteritems()])
        elif isinstance(data, collections.Iterable):
            return type(data)([Serializer.convert(x) for x in data])
        else:
            return data

class DeserializableMixin(object):
    ''' The :py:class:`DeserializableMixin` provides a mixin class
    that addes the ability to load and deserialize an object from
    a file-like object stored in a format supported by
    :py:class:`Serializer`.   Class objects using this mixin should
    define a deserialize method to automatically transform the
    contents loaded
    '''

    def loads(self, contents, content_type=CONTENT_TYPE_OTHER):
        try:
            serializer = Serializer()
            log.debug('attempting to deserialize %r with content_type %s',
                        self, content_type)
            contents = serializer.deserialize(contents, content_type)
            self.deserialize(contents)
        except NotImplementedError:
            log.error('Object must define method \'deserialize\'')
            raise SerializerError
        except Exception as exc:
            log.exception(exc)
            raise SerializerError

    def load(self, fobj, content_type=CONTENT_TYPE_OTHER):
        try:
            self.loads(fobj.read(), content_type)
        except IOError:
            log.error('Unable to load file %s', fobj.name)
            raise SerializerError
        except Exception as exc:
            log.exception(exc)
            raise SerializerError

    def load_from_file(self, filepath, content_type=CONTENT_TYPE_OTHER):
        try:
            log.debug('Attempting to read file %s', filepath)
            self.load(open(filepath), content_type)
        except IOError:
            log.error('Cannot read from file %s', filepath)
            raise SerializerError
        except Exception as exc:
            log.exception(exc)
            raise SerializerError

    def deserialize(self, contents):
        ''' objects that use this mixin must provide this method '''
        raise NotImplementedError

class SerializableMixin(object):
    ''' The :py:class:`SerializableMixin` provides a mixin class
    that addes the ability to dump and serialize an object from
    a file-like object stored in a format supported by
    :py:class:`Serializer`.  Class objects using this mixin should
    define a serialize method to automatically transform the
    contents loaded
    '''

    def dumps(self, content_type=CONTENT_TYPE_OTHER):
        try:
            serializer = Serializer()
            contents = self.serialize()
            log.debug('attempting to serialize %r with content_type %s',
                      self, content_type)
            return serializer.serialize(contents, content_type)
        except NotImplementedError:
            log.error('Object must define method \'serialize\'')
            raise SerializerError
        except Exception as exc:
            log.exception(exc)
            raise SerializerError

    def dump(self, fobj, content_type=CONTENT_TYPE_OTHER):
        try:
            contents = self.dumps(content_type)
            fobj.write(contents)
        except IOError:
            log.error('Unable to load file %s', fobj.name)
            raise SerializerError

    def dump_to_file(self, filepath, content_type=CONTENT_TYPE_OTHER):
        try:
            log.debug('Attempting to write to file %s', filepath)
            self.dump(open(filepath, 'w'), content_type)
        except IOError:
            log.error('Cannot write to file %s', filepath)
            raise SerializerError
        except Exception as exc:
            log.exception(exc)
            raise SerializerError

    def serialize(self):
        ''' objects that use this mixin must provide this method '''
        raise NotImplementedError




