# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=W0614,C0103,W0142,W1201
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

import collections
import logging
import os
import re

import ztpserver.config

from ztpserver.serializers import SerializableMixin, DeserializableMixin
from ztpserver.constants import CONTENT_TYPE_YAML

DEVICENAME_PARSER_RE = re.compile(r":(?=[Ethernet|\d+(?/)(?\d+)|\*])")
ANYDEVICE_PARSER_RE = re.compile(r":(?=[any])")
FUNC_RE = re.compile(r"(?P<function>\w+)(?=\(\S+\))\([\'|\"]"
                     r"(?P<arg>.+?)[\'|\"]\)")

log = logging.getLogger(__name__)
serializer = ztpserver.serializers.Serializer()

def log_msg(text, error=False):
    text = 'NeighborDB: %s' % text
    if error:
        text = 'ERROR: %s' % text
    log.debug(text)

class NodeErrror(Exception):
    ''' base error raised by :py:class:`Node` '''
    pass

class ResourcePoolError(Exception):
    ''' base error raised by :py:class:`Resource` '''
    pass

class TopologyError(Exception):
    ''' base error raised by :py:class:`Topology` '''
    pass

class PatternError(Exception):
    ''' base error raised by :py:class:`Pattern` '''
    pass

class OrderedCollection(collections.OrderedDict):
    ''' base object for using an ordered dictionary '''
    def __call__(self, key=None):
        #pylint: disable=W0221
        return self.keys() if key is None else self.get(key)


class Node(DeserializableMixin):

    Neighbor = collections.namedtuple("Neighbor", ['device', 'port'])

    def __init__(self, systemmac, model=None, serialnumber=None,
                 version=None, neighbors=None):

        self.systemmac = systemmac
        self.model = model
        self.serialnumber = serialnumber
        self.version = version
        self.neighbors = OrderedCollection()

        if neighbors is not None:
            self.add_neighbors(neighbors)

    def __repr__(self):
        return "Node(neighbors=%d)" % len(self.neighbors)

    def add_neighbors(self, neighbors):
        ''' adds a list of neighbors to the node object

        :param neighbors: an unordered list of neighbors
        '''
        for interface, neighbor_list in neighbors.items():
            collection = list()
            for neighbor in neighbor_list:
                device, port = neighbor.values()
                collection.append(self.Neighbor(device, port))
            self.neighbors[interface] = collection

    def deserialize(self, contents):
        for prop in ['model', 'systemmac', 'serialnumber', 'version']:
            if prop in contents:
                setattr(self, prop, contents[prop])

        self.neighbors = OrderedCollection()
        if 'neighbors' in contents:
            self.add_neighbors(contents['neighbors'])

    def serialize(self):
        attrs = dict()
        for prop in ['model', 'systemmac', 'serialnumber', 'version']:
            if getattr(self, prop) is not None:
                attrs[prop] = getattr(self, prop)

        neighbors = dict()
        if len(self.neighbors) > 0:
            for interface, neighbors in self.neighbors.items():
                collection = list()
                for neighbor in neighbors:
                    collection.append(dict(device=neighbor.device,
                                           port=neighbor.port))
                neighbors[interface] = collection
        attrs['neighbors'] = neighbors
        return attrs

class ResourcePool(DeserializableMixin, SerializableMixin):

    def __init__(self):
        filepath = ztpserver.config.runtime.default.data_root
        self.filepath = os.path.join(filepath, "resources")
        self.data = None

    def serialize(self):
        return self.data

    def deserialize(self, contents):
        self.data = contents

    def allocate(self, pool, node):
        match = self.lookup(pool, node)
        if match:
            log_msg("Found allocated resources, returning %s" % match)
            return match

        filepath = os.path.join(self.filepath, pool)
        self.load(open(filepath), CONTENT_TYPE_YAML)

        try:
            key = next(x[0] for x in self.data.items() if x[1] is None)
            self.data[key] = node.systemmac
        except StopIteration:
            raise ResourcePoolError('no resources available in pool')

        self.dump(open(filepath, 'w'), CONTENT_TYPE_YAML)
        return key

    def lookup(self, pool, node):
        log_msg("Looking up resource for node %s" % node.systemmac)

        filepath = os.path.join(self.filepath, pool)
        self.load(open(filepath), CONTENT_TYPE_YAML)

        matches = [x[0] for x in self.data.items() if x[1] == node.systemmac]
        key = matches[0] if matches else None
        return key


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

class Topology(DeserializableMixin):

    def __init__(self):
        self.variables = None
        self.patterns = None

        self.clear()

    def __repr__(self):
        return "Topology(globals=%d, nodes=%d)" % \
            (len(self.patterns['globals']), len(self.patterns['nodes']))

    def clear(self):
        self.variables = dict()
        self.patterns = {'globals': list(), 'nodes': dict()}

    def load(self, fobj, content_type=CONTENT_TYPE_YAML):
        self.clear()
        super(Topology, self).load(fobj, content_type)

    def loads(self, contents, content_type=CONTENT_TYPE_YAML):
        self.clear()
        super(Topology, self).loads(contents, content_type)

    def deserialize(self, contents):
        self.variables = contents.get('variables') or dict()

        if 'any' in self.variables or 'none' in self.variables:
            log_msg('Cannot assign value to reserved word', error=True)
            if 'any' in self.variables:
                del self.variables['any']
            if 'none' in self.variables:
                del self.variables['none']

        for pattern in contents.get('patterns'):
            pattern = self.add_pattern(**pattern)

    def add_pattern(self, name, definition, node=None, interfaces=None,
                    variables=None):

        try:
            obj = Pattern(name, definition, node=node, interfaces=interfaces,
                          variables=variables)

            # we need to do this to copy any global variables to
            # the pattern if a mores specific variable doesn't exists
            # otherwise we will not write the node pattern correctly
            # later
            if self.variables is not None:
                for item in obj.interfaces:
                    if item.device not in [None, 'any'] and \
                        item.device in self.variables:
                        item.device = self.variables[item.device]

        except TypeError:
            log_msg('Unable to parse pattern entry', error=True)
            return

        if node:
            self.patterns['nodes'][obj.node] = obj
        else:
            self.patterns['globals'].append(obj)


    def get_patterns(self, node):
        """ returns a list of possible patterns for a given node """

        log_msg("Searching for systemmac %s in patterns" % node.systemmac)
        log_msg("Available node patterns: %s" % self.patterns['nodes'].keys())

        if node.systemmac in self.patterns['nodes'].keys():
            pattern = self.patterns['nodes'].get(node.systemmac)
            log_msg("Returning node pattern[%s] for node[%s]" % \
                (pattern.name, node.systemmac))
            return [pattern]
        else:
            log_msg("Returning node pattern[globals] patterns for node[%s]"\
                % node.systemmac)
            return self.patterns['globals']

    def match_node(self, node):
        """ Returns a list of :py:class:`Pattern` classes satisfied
        by the :py:class:`Node` argument
        """

        matches = list()
        for pattern in self.get_patterns(node):
            log_msg('Attempting to match Pattern [%s]' % pattern.name)

            if pattern.match_node(node, self.variables):
                log_msg('Match for [%s] was successful' % pattern.name)
                matches.append(pattern)
            else:
                log_msg("Failed to match [%s]" % pattern.name)

        return matches

class Pattern(DeserializableMixin, SerializableMixin):

    def __init__(self, name=None, definition=None, node=None,
                 interfaces=None, variables=None):

        self.name = name
        self.definition = definition

        self.node = node
        self.variables = variables or dict()

        self.interfaces = list()
        if interfaces:
            self.add_interfaces(interfaces)

    def dumps(self, content_type=CONTENT_TYPE_YAML):
        # pylint: disable=W0221
        return super(Pattern, self).dumps(content_type)

    def deserialize(self, contents):
        self.name = contents.get('name')
        self.definition = contents.get('definition')

        self.node = contents.get('node')
        self.variables = contents.get('variables') or dict()

        self.interfaces = list()
        if 'interfaces' in contents:
            self.add_interfaces(contents.get('interfaces'))

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

    def add_interface(self, interface, device, port, tags=None):
        self.interfaces.append(InterfacePattern(interface, device, port, tags))

    def add_interfaces(self, interfaces):
        for interface in interfaces:
            for key, values in interface.items():
                args = self._parse_interface(key, values)
                log_msg("Adding interface to pattern with args %s" %
                          str(args))

                (interface, device, port, tags) = args
                self.add_interface(interface, device, port, tags)

    def _parse_interface(self, interface, values):
        log_msg("parse_interface[%s]: %s" % (str(interface), str(values)))

        device = port = tags = None
        if isinstance(values, dict):
            device = values.get('device')
            port = values.get('port')
            tags = values.get('tags')

        # handles the case of implicit 'any'
        if values == 'any' or device == 'any':
            device, port, tags = 'any', 'any', None

        # handles the case of implicit 'none'
        elif values == 'none' or device == 'none':
            device, port, tags = None, None, None

        elif isinstance(values, str):
            try:
                device, port = DEVICENAME_PARSER_RE.split(values)
            except ValueError:
                device, port = ANYDEVICE_PARSER_RE.split(values)
            port, tags = port.split(':') if ':' in port else (port, None)

        # perform variable substitution
        if device not in [None, 'any'] and device in self.variables:
            device = self.variables[device]

        return (interface, device, port, tags)

    def match_node(self, node, variables=None):
        if variables is None:
            variables = {}

        neighbors = node.neighbors.copy()

        for intf_pattern in self.interfaces:
            log_msg('Attempting to match %r' % intf_pattern)
            log_msg('Available neighbors: %s' % neighbors.keys())

            # check for device none
            if intf_pattern.device is None:
                log_msg("InterfacePattern device is 'none'")
                if [x for x in intf_pattern.interfaces if x in neighbors()]:
                    return False
                return True

            variables.update(self.variables)
            matches = intf_pattern.match_neighbors(neighbors, variables)
            if not matches:
                log_msg("InterfacePattern failed to match interface[%s]" \
                    % intf_pattern.interface)
                return False

            log_msg("InterfacePattern matched interfaces %s" % matches)
            for match in matches:
                log_msg("Removing interface %s from available pool" % match)
                del neighbors[match]

        return True

class InterfacePattern(object):

    def __init__(self, interface, device, port, tags=None):

        self.interface = interface
        self.interfaces = self.range(interface)

        self.device = device

        self.port = port
        self.ports = self.range(port)

        self.tags = tags or list()

    def __repr__(self):
        return "InterfacePattern(interface=%s, device=%s, port=%s)" % \
            (self.interface, self.device, self.port)

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

    def range(self, interface_range):
        # pylint: disable=R0201
        if interface_range is None:
            return list()
        elif not interface_range.startswith('Ethernet'):
            return [interface_range]

        indicies = re.split("[a-zA-Z]*", interface_range)[1]
        indicies = indicies.split(',')

        interfaces = list()
        for index in indicies:
            if '-' in index:
                start, stop = index.split('-')
                for index in range(int(start), int(stop)+1):
                    interfaces.append('Ethernet%s' % index)
            else:
                interfaces.append('Ethernet%s' % index)
        return interfaces

    def match_neighbors(self, neighbors, variables):
        if self.interface == 'any':
            # the pattern interface is any so we should consider
            # all neighbor interfaces as potential matches
            interfaces = neighbors()
        elif len(self.interfaces) > len(neighbors()):
            # there are not enough neighbor entries to satisfy
            # the pattern range so no reason to even try to match
            # just return an empty list
            return list()
        else:
            # the pattern interface specifies a range so
            # we can only consider those interfaces for pattern
            # matching
            interfaces = [x for x in self.interfaces if x in neighbors()]

        matches = list()
        for interface in interfaces:
            for device, port in neighbors(interface):
                if self.match_device(device, variables) and \
                   self.match_port(port):
                    matches.append(interface)
                    # as soon as a device/port match is found in the
                    # list of for this interface we don't have to check
                    # for any more matches because it succeeds
                    break
        if matches != interfaces and self.interface != 'any':
            # uh oh we didn't match all the interfaces, return an empty list
            matches = list()
        return matches

    def match_device(self, device, variables=None):
        if variables is None:
            variables = {}
        if self.device is None:
            return False
        elif self.device == 'any':
            return True
        pattern = variables.get(self.device) or self.device
        match = FUNC_RE.match(pattern)
        method = match.group('function') if match else 'exact'
        method = getattr(Functions, method)
        arg = match.group('arg') if match else pattern
        return method(arg, device)

    def match_port(self, port):
        if (self.port is None and self.device == 'any') or \
           (self.port == 'any'):
            return True
        elif self.port is None and self.device is None:
            return False
        return port in self.ports


