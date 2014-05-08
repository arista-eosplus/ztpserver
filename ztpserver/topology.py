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
# pylint: disable=W0614,C0103,W0142
#
import collections
import logging
import os
import re
import string # pylint: disable=W0402

import ztpserver.config

from ztpserver.serializers import SerializableMixin, DeserializableMixin
from ztpserver.constants import CONTENT_TYPE_YAML

ANY_DEVICE_PARSER_RE = re.compile(r':(?=[any])')
NONE_DEVICE_PARSER_RE = re.compile(r':(?=[none])')
FUNC_RE = re.compile(r'(?P<function>\w+)(?=\(\S+\))\([\'|\"]'
                     r'(?P<arg>.+?)[\'|\"]\)')

ALL_CHARS = set([chr(c) for c in range(256)])
NON_HEX_CHARS = ALL_CHARS - set(string.hexdigits)

log = logging.getLogger(__name__)
serializer = ztpserver.serializers.Serializer()

def log_msg(text, error=False):
    text = 'NeighborDB: %s' % text
    if error:
        text = 'ERROR: %s' % text
    log.debug(text)

class ResourcePoolError(Exception):
    ''' base error raised by :py:class:`Resource` '''
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
        return self.get(key) if key else self.keys()


Neighbor = collections.namedtuple('Neighbor', ['device', 'port'])


class Node(SerializableMixin, DeserializableMixin):

    def __init__(self, systemmac,
                 model=None, serialnumber=None,
                 version=None, neighbors=None):

        self.systemmac = systemmac
        self.model = model
        self.serialnumber = serialnumber
        self.version = version

        self.neighbors = OrderedCollection()
        if neighbors:
            self.add_neighbors(neighbors)

    def __repr__(self):
        return 'Node(node=%s, neighbors=%s, ...)' % \
               (self.systemmac, str(self.neighbors))

    def add_neighbors(self, neighbors):
        ''' adds a list of neighbors to the node object

        :param neighbors: an unordered list of neighbors
                          (each represented as a touple)
        '''
        for interface, neighbor_list in neighbors.iteritems():
            neighbors = []
            for neighbor in neighbor_list:
                neighbors.append(Neighbor(neighbor['device'],
                                          neighbor['port']))
            self.neighbors[interface] = neighbors

    def deserialize(self, json):
        for prop in ['model', 'node', 'serialnumber', 'version']:
            if prop in json:
                setattr(self, prop, json[prop])

        self.neighbors = OrderedCollection()
        if 'neighbors' in json:
            self.add_neighbors(json['neighbors'])

    def serialize(self):
        result = {}
        for prop in ['model', 'systemmac', 'serialnumber', 'version']:
            if getattr(self, prop):
                result[prop] = getattr(self, prop)

        neighbors = {}
        if self.neighbors:
            for interface, neighbor_list in self.neighbors.iteritems():
                serialized_neighbor_list = []
                for neighbor in neighbor_list:
                    serialized_neighbor_list.append(
                        dict(device=neighbor.device,
                             port=neighbor.port))
                neighbors[interface] = serialized_neighbor_list
        result['neighbors'] = neighbors
        return result


class ResourcePool(DeserializableMixin, SerializableMixin):

    def __init__(self):
        self.filepath = os.path.join(ztpserver.config.runtime.default.data_root,
                                     'resources')
        self.data = None

    def serialize(self):
        assert isinstance(self.data, dict)
        return self.data

    def deserialize(self, contents):
        assert isinstance(contents, dict)
        self.data = contents

    def allocate(self, pool, node):
        match = self.lookup(pool, node)
        if match:
            log_msg('Found allocated resources, returning %s' % match)
            return match

        filepath = os.path.join(self.filepath, pool)
        self.load_from_file(filepath, CONTENT_TYPE_YAML)

        try:
            key = next(x[0] for x in self.data.iteritems() if x[1] is None)
            self.data[key] = node.systemmac
        except StopIteration:
            raise ResourcePoolError('no resources available in pool')

        self.dump_to_file(filepath, CONTENT_TYPE_YAML)
        return key

    def lookup(self, pool, node):
        log_msg('Looking up resource for node %s' % node.systemmac)

        filepath = os.path.join(self.filepath, pool)
        self.load_from_file(filepath, CONTENT_TYPE_YAML)

        matches = [m[0] for m in self.data.iteritems()
                   if m[1] == node.systemmac]
        key = matches[0] if matches else None
        return key


class Functions(object):

    @classmethod
    def exact(cls, arg, value):
        return arg == value

    @classmethod
    def regex(cls, arg, value):
        return re.match(arg, value)

    @classmethod
    def includes(cls, arg, value):
        return arg in value

    @classmethod
    def excludes(cls, arg, value):
        return arg not in value


class Topology(DeserializableMixin):

    def __init__(self):
        self.global_variables = {}
        self.patterns = {'globals': [],
                         'nodes': {}}

    def __repr__(self):
        return 'Topology(variables=%d, globals=%d, nodes=%d)' % \
               (len(self.global_variables),
                len(self.patterns['globals']),
                len(self.patterns['nodes']))

    def clear(self):
        self.global_variables.clear()
        self.patterns['globals'] = []
        self.patterns['nodes'].clear()

    def load_from_file(self, filepath, content_type=CONTENT_TYPE_YAML):
        self.clear()
        super(Topology, self).load_from_file(filepath, content_type)

    def deserialize(self, contents):
        self.global_variables = contents.get('variables', {})

        reserved_variable_names = ['any', 'none']
        for var in reserved_variable_names:
            if var in self.global_variables:
                log_msg('Reserved word used for variable name: %s' % var,
                        error=True)
                del self.global_variables[var]

        for pattern in contents.get('patterns'):
            self.add_pattern(**pattern)

    def add_pattern(self, name=None, definition=None,
                    node=None, interfaces=None,
                    variables=None):
        log_msg('Adding pattern: name=%s, ...' % name)

        if not (name and (isinstance(name, (int, long, float,
                                            complex, basestring)))):
            log_msg('Failed to parse pattern because of invalid name: '
                    '%s' % str(name), error=True)
            return

        if not (definition and isinstance(definition, basestring) and
                len(definition.split()) == 1):
            log_msg('Failed to parse pattern because of invalid definition: '
                    '%s' % str(definition), error=True)
            return

        if not (interfaces and isinstance(interfaces, list)):
            log_msg('Failed to parse pattern because of invalid interfaces: '
                    '%s' % str(interfaces), error=True)
            return

        if node and \
                (not isinstance(node, basestring) or
                 len(node.translate(''.join(ALL_CHARS),
                                    ''.join(NON_HEX_CHARS))) != 12):
            log_msg('Failed to parse pattern because of invalid systemmac: '
                    '%s' % str(node), error=True)
            return

        if variables and not isinstance(variables, dict):
            log_msg('Failed to parse pattern because of '
                    'invalid variables list: %s' % str(variables), error=True)
            return

        # Compute list of variables
        pattern_variables = variables or {}
        for key in [x for x in self.global_variables
                    if x not in pattern_variables]:
            pattern_variables[key] = self.global_variables[key]

        # Create pattern
        try:
            pattern = Pattern(name, definition, interfaces,
                              node=node, variables=pattern_variables)
            log_msg('Pattern entry parsed successfully')

            # Add pattern to topology
            if node:
                self.patterns['nodes'][pattern.node] = pattern
            else:
                self.patterns['globals'].append(pattern)
        except PatternError as error:
            log_msg('Failed to parse pattern: %s' % str(error),
                    error=True)

    def node_patterns(self):
        result = []
        for entry in self.patterns['nodes'].itervalues():
            result.append(entry.name)
        return sorted(result)

    def global_patterns(self):
        return sorted([x.name for x in self.patterns['globals']])

    def all_patterns(self):
        return sorted(self.node_patterns() + self.global_patterns())

    def find_eligible_patterns(self, node):
        ''' returns a list of possible patterns for a given node '''
        log_msg('Searching for eligible patterns for node: %s' % node.systemmac)

        if node.systemmac in self.patterns['nodes']:
            pattern = self.patterns['nodes'].get(node.systemmac)
            log_msg('Eligible pattern: %s' % pattern.name)
            return [pattern]
        else:
            log_msg('Eligible patterns: all global patterns')
            return self.patterns['globals']

    def match_node(self, node):
        ''' Returns a list of :py:class:`Pattern` classes satisfied
        by the :py:class:`Node` argument
        '''

        result = []
        for pattern in self.find_eligible_patterns(node):
            log_msg('Attempting to match pattern %s' % pattern.name)

            if pattern.match_node(node):
                log_msg('Match for pattern %s succeeded' % pattern.name)
                result.append(pattern)
            else:
                log_msg('Match for pattern %s failed' % pattern.name)

        return result


class Pattern(DeserializableMixin, SerializableMixin):

    def __init__(self, name, definition, interfaces,
                 node=None, variables=None):

        self.name = name
        self.definition = definition

        self.node = node
        self.variables = variables or {}

        self.interfaces = []
        if interfaces:
            self.add_interfaces(interfaces)

        self.variable_substitution()

    def __repr__(self):
        return "Pattern(name=%s)" % self.name

    def variable_substitution(self):
        substitution = False
        for item in self.interfaces:
            if(item.remote_device and
               item.remote_device.startswith('$') and
               item.remote_device[1:] in self.variables):
                item.remote_device = self.variables[item.remote_device[1:]]
                substitution = True
            if(item.remote_interface and
               item.remote_interface.startswith('$') and
               item.remote_interface[1:] in self.variables):
                item.remote_interface = \
                    self.variables[item.remote_interface[1:]]
                substitution = True
            if substitution:
                log_msg('InterfacePattern substitution: %s' % str(item))
            substitution = False

    def deserialize(self, contents):
        self.name = contents.get('name')
        self.definition = contents.get('definition')

        self.node = contents.get('node', None)
        self.variables = contents.get('variables', {})

        self.interfaces = []
        self.add_interfaces(contents.get('interfaces', []))
        self.variable_substitution()

    def serialize(self):
        data = dict(name=self.name, definition=self.definition)

        interfaces = []
        for entry in self.interfaces:
            interfaces.append({entry.interfaces_init: entry.serialize()})
        data['interfaces'] = interfaces

        if self.variables:
            data['variables'] = self.variables

        if self.node:
            data['node'] = self.node

        return data

    def add_interface(self, interface_details):
        if not isinstance(interface_details, dict):
            raise PatternError('Expected dict, but got: %s' %
                               str(interface_details))

        for intf, peer_info in interface_details.iteritems():
            try:
                args = self.parse_interface(intf, peer_info)
                log_msg('Adding interface to pattern: %s' % str(args))
                (interface, remote_device, remote_interface) = args

                self.interfaces.append(InterfacePattern(interface,
                                                        remote_device,
                                                        remote_interface))
            except InterfacePatternError as error:
                log_msg('Could not add pattern %s because %s' %
                        (self.name, error), error=True)
                raise PatternError('Failed to create interface pattern')

    def add_interfaces(self, interfaces):
        for interface_details in interfaces:
            self.add_interface(interface_details)

    @classmethod
    def parse_interface(cls, interface, peer_info):
        log_msg('parse_interface[%s]: %s' % (str(interface), str(peer_info)))

        if isinstance(peer_info, dict):
            for key in peer_info:
                if key not in ['device', 'port']:
                    raise InterfacePatternError('Unexpected key: %s' % key)
            remote_device = peer_info.get('device', 'any')
            remote_interface = peer_info.get('port', 'any')

        elif isinstance(peer_info, basestring):
            if peer_info == 'any':
                # handles the case of implicit 'any'
                remote_device, remote_interface = 'any', 'any'
            elif peer_info == 'none':
                # handles the case of implicit 'none'
                remote_device, remote_interface = 'none', 'none'
            elif ':' not in peer_info:
                remote_device = peer_info
                remote_interface = 'any'
            else:
                tokens = peer_info.split(':')
                if len(tokens) != 2:
                    raise InterfacePatternError('Unexpected peer: %s' %
                                                peer_info)
                remote_device = tokens[0]
                remote_interface = tokens[1]
        else:
            raise InterfacePatternError('Unexpected peer: %s' % peer_info)

        remote_device = remote_device.strip()
        if len(remote_device.split()) != 1:
            raise InterfacePatternError('Unexpected peer: %s' %
                                        peer_info)
        remote_interface = remote_interface.strip()
        if len(remote_interface.split()) != 1:
            raise InterfacePatternError('Unexpected peer: %s' %
                                        peer_info)

        return (interface, remote_device, remote_interface)

    def match_node(self, node):
        log_msg('Attempting to match node: %s' % str(node))

        patterns = list(self.interfaces)
        for intf, neighbors in node.neighbors.iteritems():
            match = None
            for index, intf_pattern in enumerate(patterns):
                # True, False, None
                result = intf_pattern.match_neighbors(intf, neighbors)
                if result is True and not match:
                    log_msg('Interface %s matched %s '%
                            (intf, str(intf_pattern)))
                    match = index
                elif result is False:
                    log_msg('Failed to match node: interface %s does not '
                            'comply with %s'  %
                            (intf, str(intf_pattern)))
                    return False

            if match is not None:
                del patterns[match]
            else:
                log_msg('Failed to match node: %s does not match '
                        'any pattern'  % intf)

        for intf_pattern in patterns:
            if intf_pattern.is_positive_constraint():
                log_msg('Failed to match node: no neighbor matched %s' %
                        str(intf_pattern))
                return False

        return True


class InterfacePattern(object):

    def __init__(self, interfaces, remote_device, remote_interface):

        # Used for serialization
        self.interfaces_init = interfaces
        self.remote_device_init = remote_device
        self.remote_interface_init = remote_interface

        self.interfaces = self.parse_interfaces(interfaces)

        # Used for potential variable substitution
        self.remote_device = remote_device
        self.remote_interface = remote_interface

    def is_positive_constraint(self):
        if self.interfaces == 'any':
            if self.remote_device == 'any':
                return True
            elif self.remote_device != 'none':
                return self.remote_interface != 'none'

        elif self.interfaces != 'none':
            if self.remote_device == 'any':
                return True
            elif self.remote_device != 'none':
                return self.remote_interface != 'none'

        return False

    def __repr__(self):
        return 'InterfacePattern(interface=%s, remote_device=%s, '\
               'remote_interface=%s, remote_device_init=%s, '\
               'remote_interface_init=%s)' % (self.interfaces_init,
                                              self.remote_device,
                                              self.remote_interface,
                                              self.remote_device_init,
                                              self.remote_interface_init)

    def serialize(self):
        result = dict()
        result['device'] = self.remote_device_init or 'none'
        result['port'] = self.remote_interface_init or 'none'
        return result

    @classmethod
    def parse_interfaces(cls, interface_range):
        # pylint: disable=R0912

        def raiseError():
            raise InterfacePatternError('Unable to parse interface range: %s' %
                                        interface_range)

        if interface_range in ['any', 'none']:
            return interface_range

        if(not isinstance(interface_range, basestring) or
           not interface_range.startswith('Ethernet')):
            raiseError()

        interfaces = []
        for token in interface_range[8:].split(','):
            if '-' in token and '/' in token:
                raiseError()
            elif '-' in token:
                if len(token.split('-')) != 2:
                    raiseError()
                start, stop = token.split('-')
                try:
                    start = int(start)
                    stop = int(stop)
                    if(stop < start or
                       start < 0 or
                       stop < 0):
                        raiseError()
                    for index in range(int(start), int(stop) + 1):
                        interfaces.append('Ethernet%s' % index)
                except ValueError:
                    raiseError()
            elif '/' in token:
                tkns = token.split('/')
                if len(tkns) > 3:
                    raiseError()
                for tok in tkns:
                    try:
                        tok_int = int(tok)
                        if tok_int < 1:
                            raise ValueError
                    except ValueError:
                        raiseError()
                interfaces.append('Ethernet%s' % token)
            else:
                try:
                    tok_int = int(token)
                    if tok_int < 1:
                        raise ValueError
                except ValueError:
                    raiseError()
                interfaces.append('Ethernet%s' % token)

        return interfaces

    def match_neighbors(self, intf, neighbors):
        # pylint: disable=R0911,R0912

        log_msg('Attempting to match %s against %r' %
                (neighbors, self))

        if self.interfaces == 'any':
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    return True
                elif self.remote_interface == 'none':
                    # bogus
                    return False
                else:
                    if self.match_remote_interface(neighbors):
                        return True
            elif self.remote_device == 'none':
                if self.remote_interface == 'any':
                    # bogus
                    return False
                elif self.remote_interface == 'none':
                    # bogus
                    return False
                else:
                    return False
            else:
                if self.remote_interface == 'any':
                    if self.match_remote_device(neighbors):
                        return True
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbors):
                        return False
                else:
                    if(self.match_remote_device(neighbors) and
                       self.match_remote_interface(neighbors)):
                        return True

        elif self.interfaces == 'none':
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    # bogus
                    return False
                elif self.remote_interface == 'none':
                    # bogus
                    return False
                else:
                    if self.match_remote_interface(neighbors):
                        return False
            elif self.remote_device == 'none':
                if self.remote_interface == 'any':
                    # bogus
                    return False
                elif self.remote_interface == 'none':
                    return False
                else:
                    # bogus
                    return False
            else:
                if self.remote_interface == 'any':
                    if self.match_remote_device(neighbors):
                        return False
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbors):
                        return False
                else:
                    if(self.match_remote_device(neighbors) and
                       self.match_remote_interface(neighbors)):
                        return False
        else:
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    if intf in self.interfaces:
                        return True
                elif self.remote_interface == 'none':
                    if intf in self.interfaces:
                        return False
                else:
                    if(intf in self.interfaces and
                       self.match_remote_interface(neighbors)):
                        return True
            elif self.remote_device == 'none':
                if self.remote_interface == 'any':
                    if intf in self.interfaces:
                        return False
                elif self.remote_interface == 'none':
                    if intf in self.interfaces:
                        return False
                else:
                    if(intf in self.interfaces and
                       self.match_remote_interface(neighbors)):
                        return False
            else:
                if self.remote_interface == 'any':
                    if self.match_remote_device(neighbors):
                        return True
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbors):
                        return False
                else:
                    if(intf in self.interfaces and
                       self.match_remote_device(neighbors) and
                       self.match_remote_interface(neighbors)):
                        return True

        return None

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

    def match_remote_device(self, neighbors):
        if self.remote_device == 'any':
            return True
        elif self.remote_device is None:
            return False
        elif FUNC_RE.match(self.remote_device):
            for neighbor in neighbors:
                if self.run_function(self.remote_device,
                                     neighbor.device):
                    return True
            return False
        else:
            for neighbor in neighbors:
                if self.remote_device == neighbor.device:
                    return True
            return False

    def match_remote_interface(self, neighbors):
        if self.remote_interface == 'any':
            return True
        elif self.remote_interface is None:
            return False
        elif FUNC_RE.match(self.remote_interface):
            for neighbor in neighbors:
                if self.run_function(self.remote_interface,
                                     neighbor.port):
                    return True
            return False
        else:
            for neighbor in neighbors:
                if self.remote_interface == neighbor.port:
                    return True
            return False
