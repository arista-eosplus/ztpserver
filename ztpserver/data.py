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
import re
import collections

import ztpserver.config
import ztpserver.serializers

DEVICENAME_PARSER_RE = re.compile(":(?=[Ethernet|\d+(?/)(?\d+)|\*])")
ANYDEVICE_PARSER_RE = re.compile(":(?=[any])")
FUNC_RE = re.compile("(?P<function>\w+)(?=\(\S+\))\([\'|\"](?P<arg>.+?)[\'|\"]\)")

serializer = ztpserver.serializers.Serializer()

class Collection(collections.Mapping, collections.Callable):
    def __init__(self):
        self.data = dict()

    def __call__(self, key=None):
        if key is None:
            return self.keys()
        else:
            return self.get(key)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class OrderedCollection(collections.OrderedDict, collections.Callable):
    def __call__(self, key=None):
        if key is None:
            return self.keys()
        else:
            return self.get(key)

class Interface(object):
    """ The :py:class:`'Interface' object represents a single
    node interface and all associated neighbors
    """

    LldpNeighbor = collections.namedtuple("LldpNeighbor", ['device', 'port'])

    def __init__(self, name):
        self.name = name
        self.neighbors = list()

    def __repr__(self):
        return "Interface(name=%s, neighbor_count=%d)" % \
            (self.name, len(self.neighbors))

    def add_neighbor(self, device, port):
        self.neighbors.append(self.LldpNeighbor(device, port))


class Interfaces(OrderedCollection):
    """ The :py:class:`Interfaces` object is a container for holding
    node interface data of type :py:class:`Interface`
    """

    def __repr__(self):
        return "Interfaces(count=%d)" % len(self)

    def add_interface(self, obj):
        if isinstance(obj, str):
            obj = Interface(obj)
        elif not isinstance(obj, Interface):
            raise TypeError("argument of type %s is not supported" % type(obj))
        self[obj.name] = obj

    def add_interfaces(self, interface_list):
        if not isinstance(interface_list, list):
            raise TypeError("argument must be a list")
        for name in interface_list:
            self.add_interface(name)


class Node(object):
    """ The :py:class:`Node` object is an instantiation of the
    network element
    """

    def __init__(self):
        self.model = None
        self.systemmac = None
        self.serialnumber = None
        self.version = None
        self.interfaces = Interfaces()

        super(Node, self).__init__()

    def add_interface(self, name):
        if not name.startswith("Ethernet"):
            raise TypeError("interface name is invalid")
        self.interfaces.add_interface(name)
        return self.interfaces(name)

    def add_interfaces(self, interface_list):
        collection = list()
        for name in interface_list:
            self.add_interface(name)
            collection.append(self.interfaces(name))
        return collection


class NodeDb(Collection):

    def __repr__(self):
        return "NodeDb(entries=%d)" % len(self.data)

    def load(self, filename):
        contents = serializer.deserialize(open(filename).read(),
                                          'application/yaml')

        for k,v in contents.items():
            self.data[str(k)] = v


class Functions(object):

    @classmethod
    def exact(self, arg, value):
        return arg == value

    @classmethod
    def regex(self, arg, value):
        m = re.match(arg, value)
        return True if m else False

    @classmethod
    def includes(self, arg, value):
        return arg in value

    @classmethod
    def excludes(self, arg, value):
        return arg not in value

class NeighborDb(object):

    def __init__(self):
        self.variables = dict()

        self.patterns = dict()
        self.patterns['global'] = dict()
        self.patterns['nodes'] = dict()

    def load(self, filename):
        contents = serializers.deserialize(open(filename).read(),
                                           'application/yaml')

        self.variables = contents.get('variables') or dict()
        if 'any' in self.variables or 'none' in self.variables:
            raise ValueError("cannot assign value to reserved word")

        for pattern in contents.get('patterns'):
            name = pattern['name']
            definition = pattern['definition']

            obj = Pattern(name, definition)
            obj.variables = pattern.get('variables')

            for interface in pattern['interfaces']:

                for key, values in interface.items():
                    args = self._parse_interface(key, values)
                    obj.add_interface(*args)

            if 'node' in pattern:
                obj.node = pattern['node']
                self.patterns['nodes'][obj.node] = obj
            else:
                self.patterns['global'][id(obj)] = obj

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

        return (interface, device, port, tags)



class InterfacePattern(object):

    def __init__(self, interface, node, port, tags=None):
        self.interface = interface
        self.node = node
        self.port = port
        self.tags = tags

    def __repr__(self):
        return "InterfacePattern(interface=%s, node=%s, port=%s)" %\
            (self.interface, self.node, self.port)

    def _match_interfaces(self, pattern, interface_set):

        indicies = lambda x: re.split("[a-zA-Z]*", x)[1]

        pattern = indicies(pattern)
        pattern = pattern.split(',')

        pattern_set = list()

        for item in pattern:
            if '-' in item:
                start, stop = item.split('-')
                for z in range(int(start), int(stop)+1):
                    pattern_set.append("Ethernet%d" % z)
            else:
                pattern_set.append("Ethernet%s" % item)

        result = [i for i in pattern_set if i in interface_set]
        if len(pattern_set) != len(result):
            result = None

        return result

    def match_interfaces(self, interface_set):
        return self._match_interfaces(self.interface, interface_set)

    def match_node(self, neighbor):

        if self.node is None:
            return neighbor is None

        m = FUNC_RE.match(self.node)

        method = m.group('function') if m else 'exact'
        method = getattr(functions, method)
        arg = m.group('arg') if m else self.node

        return method(arg, neighbor)

    def match_port(self, neighbor_port):
        if self.port == 'any' or (self.port is None and self.node is not None):
            return True
        result = self._match_interfaces(self.port, neighbor_port)
        return False if result is None else True


class Pattern(object):

    def __init__(self, name, definition, **kwargs):

        self.name = name
        self.definition = definition

        self.node = kwargs.get('node')

        self.variables = kwargs.get('variables') or dict()
        self.interfaces = kwargs.get('interfaces') or list()

    def add_interface(self, interface, node, port, tags=None):
        self.interfaces.append(InterfacePattern(interface, node, port, tags))


