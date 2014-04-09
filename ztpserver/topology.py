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
NONEDEVICE_PARSER_RE = re.compile(r":(?=[none])")
FUNC_RE = re.compile(r"(?P<function>\w+)(?=\(\S+\))\([\'|\"]"
                     r"(?P<arg>.+?)[\'|\"]\)")

log = logging.getLogger(__name__)
serializer = ztpserver.serializers.Serializer()

def log_msg(text, error=False):
    text = 'NeighborDB: %s' % text
    if error:
        text = 'ERROR: %s' % text
    print text
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

class InterfacePatternError(Exception):
    ''' base error raised by :py:class:`InterfacePattern` '''
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
            for interface, attribs in self.neighbors.items():
                collection = list()
                for attrib in attribs:
                    collection.append(dict(device=attrib.device,
                                           port=attrib.port))
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

    def add_pattern(self, name=None, definition=None,
                    node=None, interfaces=None,
                    variables=None):
        log_msg('add_pattern(name=%s, ...)' % name)
        try:
            if not (name and
                    (isinstance(name, basestring) or
                     isinstance(name, (int, long, float, complex))) and
                    definition and isinstance(definition, basestring) and
                    interfaces and isinstance(interfaces, list)):
                raise TypeError

            obj = Pattern(name, definition, node=node, interfaces=interfaces,
                          variables=variables)

            # we need to do this to copy any global variables to
            # the pattern if a mores specific variable doesn't exists
            # otherwise we will not write the node pattern correctly
            # later
            if self.variables:
                for key in [x for x in self.variables
                            if x not in obj.variables]:
                    obj.variables[key] = self.variables[key]

             # TODO - variable substitution
             # for item in obj.interfaces:
             #     if item.device not in [None, 'any'] and \
             #         item.device in self.variables:
             #         item.device = self.variables[item.device]

        except TypeError:
            log_msg('Unable to parse pattern entry', error=True)
            return
        except PatternError:
            log_msg('Unable to add pattern due to PatternError', error=True)
            return

        log_msg('Pattern entry parsed successfully', error=True)
        if node:
            self.patterns['nodes'][obj.node] = obj
        else:
            self.patterns['globals'].append(obj)

    def node_patterns(self):
        result = []
        for entry in self.patterns['nodes'].itervalues():
            result.append(entry.name)
        return sorted(result)

    def global_patterns(self):
        return sorted([x.name for x in self.patterns['globals']])

    def all_patterns(self):
        return sorted(self.node_patterns() + self.global_patterns())

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

            if pattern.match_node(node):
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
        data['variables'] = self.variables

        if self.node:
            data['node'] = self.node

        interfaces = list()
        for entry in self.interfaces:
            interfaces.append({entry.interface: entry.serialize()})
        data['interfaces'] = interfaces
        return data

    def add_interface(self, interface, device, port, tags=None):
        try:
            self.interfaces.append(InterfacePattern(interface, device, port, \
                                                    tags, self.variables))
        except InterfacePatternError:
            log_msg('Could not add pattern due to invalid interface')
            raise PatternError

    def add_interfaces(self, interfaces):
        for interface in interfaces:

            if not isinstance(interface, dict):
                raise TypeError

            for key, values in interface.items():
                args = self._parse_interface(key, values)
                log_msg("Adding interface to pattern with args %s" %
                          str(args))

                (interface, device, port, tags) = args
                self.add_interface(interface, device, port, tags)

    @classmethod
    def _parse_interface(cls, interface, peer_info):
        log_msg("parse_interface[%s]: %s" % (str(interface), str(peer_info)))

        # See #32
        tags = None

        if isinstance(peer_info, dict):
            for key in peer_info:
                if key not in ['device', 'port']:
                    raise TypeError
            device = peer_info.get('device', 'any')
            port = peer_info.get('port', 'any')

        elif isinstance(peer_info, basestring):
            if peer_info == 'any':
                # handles the case of implicit 'any'
                device, port = 'any', 'any'
            elif peer_info == 'none':
                # handles the case of implicit 'none'
                device, port = None, None
            elif ':' not in peer_info:
                device = peer_info
                port = 'any'
            else:
                try:
                    device, port = DEVICENAME_PARSER_RE.split(peer_info)
                except ValueError:
                    try:
                        device, port = ANYDEVICE_PARSER_RE.split(peer_info)
                    except ValueError:
                        try:
                            device, port = \
                                NONEDEVICE_PARSER_RE.split(peer_info)
                        except ValueError:
                            raise TypeError
        else:
            raise TypeError

        # See #37. Should we perform variable substitution for
        # the port as well?
        # if device in self.variables:
        #     device = self.variables[device]

        return (interface, device, port, tags)

    def match_node(self, node):
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

            matches = intf_pattern.match_neighbors(neighbors)
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

    def __init__(self, interface, device, port, tags=None, variables=None):

        self.interface = interface
        self.interfaces = self.range(interface)

        self.device = device

        # Used for serialization
        self.port_init = port
        
        # Used for potential variable substitution 
        self.port = port

        self.tags = tags or list()

        self.variables = variables or dict()

    def __repr__(self):
        return "InterfacePattern(interface=%s, device=%s, port=%s)" % \
            (self.interface, self.device, self.port_init)

    def serialize(self):
        obj = dict()
        if self.device is None:
            obj['device'] = 'none'
        else:
            obj['device'] = self.device
            obj['port'] = self.port_init
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

        interface_name = 'Ethernet'
        if '/' in indicies:
            if indicies.count('/') > 2:
                log.debug('Could not parse interface index: %s' % indicies)
                raise InterfacePatternError
            module, indicies = indicies.split('/')
            try:
                assert int(module) > 0
                interface_name += '%s/' % module
            except (ValueError, AssertionError):
                log.debug('Could not parse interface module')
                raise InterfacePatternError

        indicies = indicies.split(',')

        interfaces = list()
        for index in indicies:
            if '-' in index:
                start, stop = index.split('-')
                try:
                    for index in range(int(start), int(stop)+1):
                        assert int(index) > 0
                        interfaces.append('%s%s' % (interface_name, index))
                except (ValueError, AssertionError):
                    log.debug('Interface index is invalid')
                    raise InterfacePatternError
            else:
                try:
                    assert int(index) > 0
                    interfaces.append('%s%s' % (interface_name, index))
                except (ValueError, AssertionError):
                    log.debug('Interface index is invalid')
                    raise InterfacePatternError
        return interfaces

    def match_neighbors(self, neighbors):
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
                if self.match_device(device) and \
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

    @classmethod
    def run_function(cls, function, argument):
        match = FUNC_RE.match(function)
        if not match:
            method = 'exact'
            arg = function
        else:
            method = getattr(Functions, match.group('function'))
            arg = match.group('arg')
        return method(arg, argument)      

    def match_device(self, device):
        f self.device == 'any':
            return True
        elif self.device is None:
            return False
        elif self.device.startswith('$'):
            return self.run_function(self.device, device)
        else:
            return self.device == device

    def match_port(self, port):
        if self.port == 'any':
            return True
        elif self.port is None:
            return False
        elif self.port.startswith('$'):
            return self.run_function(self.port, port)            
        else:
            return port == self.port


