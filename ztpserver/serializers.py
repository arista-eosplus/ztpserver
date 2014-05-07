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
    """ base error raised by serialization functions """
    pass

class YAMLSerializer(object):
    """ The :py:class:`YAMLSerializer` class will generate a
    RuntimeWarning if the PyYaml module is unavialable
    """

    def __new__(cls):
        if not YAML_AVAILABLE:
            warnings.warn('Unable to import YAML', RuntimeWarning)
            return None
        else:
            return super(YAMLSerializer, cls).__new__(cls)

    def deserialize(self, data):
        try:
            contents = yaml.safe_load(data)

        except yaml.YAMLError as exc:
            log.debug(exc)
            contents = None

        return contents

    def serialize(self, data, safe_dump=False):
        if safe_dump:
            return yaml.safe_dump(data, default_flow_style=False)
        return yaml.dump(data, default_flow_style=False)

class JSONSerializer(object):

    def deserialize(self, data):
        ''' deserialize a JSON object and return a dict '''

        assert isinstance(data, basestring)
        return json.loads(data)

    def serialize(self, data):
        ''' serialize a dict object and return JSON '''

        assert isinstance(data, dict)
        return json.dumps(data)

class Serializer(object):
    """ The :py:class:`Serializer` will serialize a data structure
    based on the content-type.   If the content-type is not supported
    the :py:class:`Serializer` will simply return the data as a
    :py:class:`str` object
    """



    def serialize(self, data, content_type, **kwargs):
        """ serialize the data base on the content_type

        If a valid handler does not exist for the requested
        content_type, then the data is returned as a string

        :param data: data to be serialized
        :param content_type: string specifies the serialize
                             handler to use

        """
        #pylint: disable=E1103
        try:
            data = self.convert(data)
            handler = self._serialize_handler(content_type)
            return handler.serialize(data, **kwargs) if handler else str(data)

        except Exception:
            raise SerializerError('Could not serialize data %s:' % data)

    def deserialize(self, data, content_type, **kwargs):
        """ deserialize the data based on the content_type

        If a valid handler does not exist for the requested
        content_type, then the data is returned as a string

        :param data: data to be deserialized
        :param content_type: string specifies the deserialize
                             handler to use

        """

        try:
            handler = self._deserialize_handler(content_type)
            data = handler.deserialize(data, **kwargs) if handler else str(data)
            data = self.convert(data)
            return data

        except Exception:
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

    @classmethod
    def convert(cls, data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict([cls.convert(x) for x in data.iteritems()])
        elif isinstance(data, collections.Iterable):
            return type(data)([cls.convert(x) for x in data])
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
        serializer = Serializer()
        log.debug('attempting to deserialize %r with content_type %s',
                  self, content_type)
        contents = serializer.deserialize(contents, content_type)
        self.deserialize(contents)

    def load(self, fobj, content_type=CONTENT_TYPE_OTHER):
        try:
            self.loads(fobj.read(), content_type)
        except IOError as exc:
            log.debug(exc)
            raise SerializerError('unable to load file')

    def load_from_file(self, filepath, content_type=CONTENT_TYPE_OTHER):
        try:
            self.load(open(filepath), content_type)
        except IOError as exc:
            log.error('Cannot read from file %s (bad permissions?)', filepath)
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
        serializer = Serializer()
        contents = self.serialize()
        log.debug('attempting to serialize %r with content_type %s',
                  self, content_type)
        return serializer.serialize(contents, content_type)

    def dump(self, fobj, content_type=CONTENT_TYPE_OTHER):
        try:
            contents = self.dumps(content_type)
            fobj.write(contents)
        except IOError as exc:
            log.error(exc)
            log.exception(exc)
            raise SerializerError

    def dump_to_file(self, filepath, content_type=CONTENT_TYPE_OTHER):
        log.debug('Writing to file %s', filepath)
        try:
            self.dump(open(filepath, 'w'), content_type)
        except IOError as exc:
            log.error('Cannot write to file %s (bad permissions?)', filepath)
            log.exception(exc)
            raise SerializerError

    def serialize(self):
        ''' objects that use this mixin must provide this method '''
        raise NotImplementedError




