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
import re
import collections

import ztpserver.config
import ztpserver.serializers

from ztpserver.constants import *

DEVICENAME_PARSER_RE = re.compile(r":(?=[Ethernet|\d+(?/)(?\d+)|\*])")
ANYDEVICE_PARSER_RE = re.compile(r":(?=[any])")
FUNC_RE = re.compile(r"(?P<function>\w+)(?=\(\S+\))\([\'|\"](?P<arg>.+?)[\'|\"]\)")

serializer = ztpserver.serializers.Serializer() # pylint: disable=C0103

class Collection(collections.Mapping, collections.Callable):
    def __init__(self):
        self.data = dict()

    def __call__(self, key=None):
        #pylint: disable=W0221
        return self.keys() if key is None else self.get(key)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class OrderedCollection(collections.OrderedDict, collections.Callable):
    def __call__(self, key=None):
        #pylint: disable=W0221
        return self.keys() if key is None else self.get(key)

class Node(object):

    Neighbor = collections.namedtuple("Neighbor", ['device', 'port'])

    def __init__(self, **kwargs):
        self.model = kwargs.get('model')
        self.systemmac = kwargs.get('systemmac')
        self.serialnumber = kwargs.get('serialnumber')
        self.version = kwargs.get('version')

        self.neighbors = OrderedCollection()
        if 'neighbors' in kwargs:
            self.add_neighbors(kwargs['neighbors'])

        super(Node, self).__init__()

    def add_neighbors(self, neighbors):
        for interface, neighbor_list in neighbors.items():
            collection = list()
            for neighbor in neighbor_list:
                collection.append(self.Neighbor(**neighbor))
            self.neighbors[interface] = collection

    def hasneighbors(self):
        return len(self.neighbors) > 0

    def serialize(self):
        attrs = dict()
        for prop in ['model', 'systemmac', 'serialnumber', 'version']:
            if getattr(self, prop) is not None:
                attrs[prop] = getattr(self, prop)

        neighbors = dict()
        if self.hasneighbors():
            for interface, neighbors in self.neighbors.items():
                collection = list()
                for neighbor in neighbors:
                    collection.append(dict(device=neighbor.device,
                                           port=neighbor.port))
                neighbors[interface] = collection
        attrs['neighbors'] = neighbors


class Functions(object):

    @classmethod
    def exact(cls, arg, value):
        return arg == value

    @classmethod
    def regex(cls, arg, value):
        match = re.match(arg, value)
        return True if match else False

    @classmethod
    def includes(cls, arg, value):
        return arg in value

    @classmethod
    def excludes(cls, arg, value):
        return arg not in value



class NeighborDb(object):

    def __init__(self, contents=None):
        self.variables = dict()
        self.patterns = {'globals': list(), 'nodes': dict()}

        if contents is not None:
            self.deserialize(contents)

    def load(self, filename):
        contents = serializer.deserialize(open(filename).read(),
                                          CONTENT_TYPE_YAML)
        self.deserialize(contents)

    def deserialize(self, contents):
        self.variables = contents.get('variables') or dict()
        if 'any' in self.variables or 'none' in self.variables:
            log.debug('cannot assign value to reserved word')
            if 'any' in self.variables:
                del self.variables['any']
            if 'none' in self.variables:
                del self.variables['none']

        for pattern in contents.get('patterns'):
            pattern = self.add_pattern(pattern)

    def add_pattern(self, pattern):

        try:
            obj = Pattern(**pattern)

            if self.variables is not None:
                for item in obj.interfaces:
                    if item.device not in [None, 'any'] and \
                        item.device in self.variables:
                        item.device = self.variables[item.device]

        except TypeError:
            log.debug('Unable to parse pattern entry')
            return

        if 'node' in pattern:
            self.patterns['nodes'][obj.node] = obj
        else:
            self.patterns['globals'].append(obj)


    def get_patterns(self, node):
        """ returns a list of possible patterns for a given node """

        if node in self.patterns['nodes'].keys():
            return [self.patterns['nodes'].get(node)]
        else:
            return self.patterns['globals']



class Pattern(object):

    def __init__(self, name, definition, **kwargs):

        self.name = name
        self.definition = definition

        self.node = kwargs.get('node')
        self.variables = kwargs.get('variables') or dict()

        self.interfaces = list()
        if 'interfaces' in kwargs:
            self.add_interfaces(kwargs['interfaces'])

    def add_interface(self, interface, device, port, tags=None):
        self.interfaces.append(InterfacePattern(interface, device, port, tags))

    def add_interfaces(self, interfaces):
        for interface in interfaces:
            for key, values in interface.items():
                args = self._parse_interface(key, values)
                self.add_interface(*args) #pylint: disable=W0142

    def _parse_interface(self, interface, values):

        if isinstance(values, dict):
            device = values.get('device')
            port = values.get('port')
            tags = values.get('tags')

        elif values == 'any':
            device, port, tags = 'any', 'any', None

        elif values == 'none':
            device, port, tags = None, None, None

        else:
            try:
                device, port = DEVICENAME_PARSER_RE.split(values)
            except ValueError:
                device, port = ANYDEVICE_PARSER_RE.split(values)
            port, tags = port.split(':') if ':' in port else (port, None)

        #perform variable substitution
        if device not in [None, 'any'] and device in self.variables:
            device = self.variables[device]

        return (interface, device, port, tags)


    def serialize(self):
        data = dict(name=self.name, definition=self.definition)
        data['variables'] = self.variables or dict()

        if self.node:
            data['node'] = self.node

        interfaces = list()
        for entry in self.interfaces:
            interfaces.append({entry.interface: entry.serialize()})
        data['interfaces'] = interfaces
        return data


class InterfacePattern(object):

    def __init__(self, interface, device, port, tags=None):
        self.interface = interface
        self.device = device
        self.port = port
        self.tags = tags or list()

    def _match_interfaces(self, pattern, interface_set, match_all=True):

        indicies = lambda x: re.split("[a-zA-Z]*", x)[1]

        pattern = indicies(pattern)
        pattern = pattern.split(',')

        pattern_set = list()
        for item in pattern:
            if '-' in item:
                start, stop = item.split('-')
                for index in range(int(start), int(stop)+1):
                    pattern_set.append("Ethernet%d" % index)
            else:
                pattern_set.append("Ethernet%s" % item)

        result = [i for i in pattern_set if i in interface_set]
        if len(result) == 0:
            result = None
        elif match_all and (len(pattern_set) != len(result)):
            result = None

        return result

    def match_interfaces(self, interface_set):
        return self._match_interfaces(self.interface, interface_set)

    def match_device(self, nbrdevice):
        if self.device is None:
            return nbrdevice is None
        match = FUNC_RE.match(self.node)
        method = match.group('function') if match else 'exact'
        method = getattr(Functions, method)
        arg = match.group('arg') if match else self.device
        return method(arg, nbrdevice)

    def match_port(self, nbrport):
        if self.port == 'any' or \
          (self.port is None and  self.device is not None):
            return True
        result = self._match_interfaces(self.port, [nbrport], False)
        return False if result is None else True

    def serialize(self):
        obj = dict()
        if self.device is None:
            obj['device'] = 'none'
        else:
            obj['device'] = self.device
            obj['port'] = self.port
        if self.tags is not None:
            obj['tags'] = self.tags
        return obj



