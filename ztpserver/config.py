# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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
import os
import collections
import ConfigParser

import ztpserver.types

class Attr(object):
    """ Base Attribute class for deriving all attributes for a Config object

    :param name: required argument specifies attribute name
    :param type: optional keyword argument specifies attribute type.  the
                 default argument type is String
    :param group: optional keyword argument specifies attribute group.  All
                  attribute names must be unique within the group
    :param default: optional keyword argument specifies the default value for
                    the attribute.  The default value is None

    """

    def __init__(self, name, **kwargs):

        self.name = name
        self.type = kwargs.get('type') or ztpserver.types.String()
        self.group = kwargs.get('group') or 'default'
        self.default = kwargs.get('default')
        self.environ = kwargs.get('environ')

        if self.environ is not None and self.environ in os.environ:
            self.default = self.type(os.environ.get(self.environ))
        elif self.default is not None:
            self.default = self.type(self.default)

    def __repr__(self):
        return 'Attr(name=%s, group=%s, default=%s)' %\
            (self.name, self.group, self.default)


class StrAttr(Attr):
    """ String attribute class derived from Attr

    :param choices: optional keyword argument specifies valid choices
    """

    def __init__(self, name, choices=None, **kwargs):
        self.choices = choices
        attrtype = ztpserver.types.String(choices=choices)
        super(StrAttr, self).__init__(name, type=attrtype, **kwargs)

class IntAttr(Attr):
    """ Integer attribute class derived from Attr

    :param minvalue: specifies the min value.  the default is None
    :param maxvalue: specifies the max value.  the default is None

    """

    def __init__(self, name, minvalue=None, maxvalue=None, **kwargs):
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        attrtype = ztpserver.types.Integer(minvalue=minvalue, maxvalue=maxvalue)
        super(IntAttr, self).__init__(name, type=attrtype, **kwargs)

class BoolAttr(Attr):
    """ Boolean attribute class derived from Attr """

    def __init__(self, name, **kwargs):
        attrtype = ztpserver.types.Boolean()
        super(BoolAttr, self).__init__(name, type=attrtype, **kwargs)

class ListAttr(Attr):
    """ List attribute class derived from Attr

    :param delimiter: specifies the delimiter character to split the string on

    """

    def __init__(self, name, delimiter=',', **kwargs):
        attrtype = ztpserver.types.List(delimiter=delimiter)
        super(ListAttr, self).__init__(name, type=attrtype, **kwargs)

class Group(collections.Mapping):
    """ The Group class provides a logical grouping of attributes in a
    Config object.   Group names must be unique for each Config instance
    and cannot be assigned values.

    :param name: the name of the group
    :param config: the config object the group is associated with

    """

    def __init__(self, name, config):
        self.name = name
        self.config = config

    def __getattr__(self, name):
        return self.config._get_attribute(name, self.name) # pylint: disable=W0212

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __iter__(self):
        return iter(self._keys())

    def __len__(self):
        return len(self._keys())

    def _keys(self):
        return [key[1] for key in self.config if key[0] == self.name]

    def add_attribute(self, item):
        self.config.add_attribute(item, self.name)


class Config(collections.Mapping):
    """ The Config class represents the configuration for collection.  """

    def __init__(self):
        self._attributes = dict()
        self._groups = list()

    def __getattr__(self, name):
        return self._get_attribute(name)

    def __getitem__(self, name):
        return self._get_attribute(name)

    def __iter__(self):
        return iter(self._attributes)

    def __len__(self):
        return len(self._attributes)

    def __repr__(self):
        return 'Config'

    def _get_attribute(self, name, group=None):
        if not group and name in self._groups:
            return Group(name, self)

        key = (group, name)
        if key not in self._attributes:
            raise AttributeError('attribute %s does not exist' % str(key))

        item = self._attributes.get(key)
        return item.get('value')

    def add_attribute(self, item, group=None):

        obj = dict(_metadata=item)

        if group is None and hasattr(item, 'group'):
            group = item.group

        key = (group, item.name)

        if group not in self._groups:
            self.add_group(group)

        if key in self._attributes:
            raise AttributeError('item already exists')

        self._attributes[key] = obj
        if item.default is not None:
            obj['value'] = self._transform(obj, item.default)

    def add_group(self, group):
        if isinstance(group, Group):
            self._groups.append(group.name)
        else:
            group = str(group)
            self._groups.append(group)

    def _transform(self, item, value):
        return item['_metadata'].type(value)

    def set_value(self, name, value, group=None):
        if not group and name in self._groups:
            raise AttributeError('cannot set a value for a group')

        item = self._attributes.get((group, name))
        if item is None:
            raise AttributeError('item does not exist')
        item['value'] = self._transform(item, value)

    def clear_value(self, name, group=None):
        """ clears the attributes value and resets it to default """

        if not group and name in self._groups:
            raise AttributeError('cannot clear values for a group')

        item = self._attributes.get((group, name))

        if item['_metadata'].default is None:
            item['value'] == None
        else:
            item['value'] = self._transform(item, item['_metadata'].default)

    def read(self, filename):
        cp = ConfigParser.ConfigParser() #pylint: disable=C0103
        cp.read(filename)

        for section in cp.sections():
            for key, value in cp.items(section):
                try:
                    self.set_value(key, value, section)
                except AttributeError:
                    continue

runtime = Config() #pylint: disable=C0103

# Group: default
runtime.add_attribute(StrAttr(
    name='data_root',
    default='/var/lib/ztpserver',
    environ='ZTPS_DATA_ROOT'
))

runtime.add_attribute(StrAttr(
    name='bootstrap_file',
    default='default'
))

runtime.add_attribute(StrAttr(
    name='definition',
    default='default',
    environ='ZTPS_DEFAULT_DEFINITION'
))

runtime.add_attribute(StrAttr(
    name='identifier',
    choices=['systemmac', 'serialnum'],
    default='systemmac'
))

runtime.add_attribute(StrAttr(
    name='server_url',
    default='http://ztpserver:8080'
))

runtime.add_attribute(BoolAttr(
    name='logging',
    default=False,
    environ='ZTPS_LOGGING'
))

runtime.add_attribute(BoolAttr(
    name='console_logging',
    default=True
))

# Group: syslog
runtime.add_attribute(BoolAttr(
    name='enabled',
    group='syslog',
    default=False
))

runtime.add_attribute(ListAttr(
    name='servers',
    group='syslog'
))

runtime.add_attribute(StrAttr(
    name='level',
    choices=['info', 'debug'],
    default='debug',
    group='syslog'
))

# Group: server
runtime.add_attribute(StrAttr(
    name='interface',
    group='server',
    default='0.0.0.0'
))

runtime.add_attribute(IntAttr(
    name='port',
    group='server',
    minvalue=1,
    maxvalue=65534,
    default=8080
))

# Group: db
runtime.add_attribute(StrAttr(
    name='nodedb',
    group='db',
    default='nodedb',
    environ='ZTPS_NODEDB'
))

runtime.add_attribute(StrAttr(
    name='neighbordb',
    group='db',
    default='neighbordb',
    environ='ZTPS_NEIGHBORDB'
))

