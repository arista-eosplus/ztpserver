# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=R0201
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
import warnings
import json

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

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
        return yaml.load(data)

    def serialize(self, data):
        return yaml.dump(data, default_flow_style=False)

class JSONSerializer(object):

    def deserialize(self, data):
        return json.loads(data)

    def serialize(self, data):
        return json.dumps(data)

# TODO refacter this whole module as functions
class Serializer(object):
    """ The :py:class:`Serializer` will serialize a data structure
    based on the content-type.   If the content-type is not supported
    the :py:class:`Serializer` will simply return the data as a
    :py:class:`str` object
    """

    def serialize(self, data, content_type):
        """ serialize the data base on the content_type

        If a valid handler does not exist for the requested
        content_type, then the data is returned as a string

        :param data: data to be serialized
        :param content_type: string specifies the serialize
                             handler to use

        """

        try:
            handler = self._serialize_handler(content_type)
            return handler.serialize(data) if handler else str(data)

        except TypeError:
            raise SerializerError('Could not serialize data')

    def deserialize(self, data, content_type):
        """ deserialize the data base on the content_type

        If a valid handler does not exist for the requested
        content_type, then the data is returned as a string

        :param data: data to be deserialized
        :param content_type: string specifies the deserialize
                             handler to use

        """

        try:
            handler = self._deserialize_handler(content_type)
            return handler.deserialize(data) if handler else str(data)

        except Exception:
            raise SerializerError('Could not deserialize data')


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
