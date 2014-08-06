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
import re
import string # pylint: disable=W0402

from ztpserver.serializers import Serializer
from ztpserver.utils import expand_range

ANY_DEVICE_PARSER_RE = re.compile(r':(?=[any])')
NONE_DEVICE_PARSER_RE = re.compile(r':(?=[none])')
FUNC_RE = re.compile(r'(?P<function>\w+)(?=\(\S+\))\([\'|\"]'
                     r'(?P<arg>.+?)[\'|\"]\)')

ALL_CHARS = set([chr(c) for c in range(256)])
NON_HEX_CHARS = ALL_CHARS - set(string.hexdigits)

log = logging.getLogger(__name__)
serializer = Serializer()


class NodeError(Exception):
    ''' Base exception class for :py:class:`Node` '''
    pass


class PatternError(Exception):
    ''' Base exception class for :py:class:`Pattern` '''
    pass


class InterfacePatternError(Exception):
    ''' Base exception class for :py:class:`InterfacePattern` '''
    pass


class TopologyError(Exception):
    ''' Base exception class for :py:class:`Topology` '''
    pass


class OrderedCollection(collections.OrderedDict):
    ''' base object for using an ordered dictionary '''
    def __call__(self, key=None):
        #pylint: disable=W0221
        return self.get(key) if key else self.keys()


class Function(object):
    def __init__(self, value):
        self.value = value

    def match(self, arg):
        raise NotImplementedError


class IncludesFunction(Function):
    def match(self, arg):
        return self.value in arg


class ExcludesFunction(Function):
    def match(self, arg):
        return self.value not in arg


class RegexFunction(Function):
    def match(self, arg):
        match = re.match(self.value, arg)
        return match is not None


class ExactFunction(Function):
    def match(self, arg):
        return arg == self.value


Neighbor = collections.namedtuple('Neighbor', ['device', 'interface'])


class Node(object):
    ''' A Node object is maps the metadata from an EOS node.  It provides
    access to the node's meta data including interfaces and the
    associated neighbors found on those interfaces.
    '''

    def __init__(self, **kwargs):
        self.systemmac = kwargs.get('systemmac')
        self.model = kwargs.get('model')
        self.serialnumber = kwargs.get('serialnumber')
        self.version = kwargs.get('version')

        self.neighbors = OrderedCollection()
        if 'neighbors' in kwargs:
            self.add_neighbors(kwargs['neighbors'])

    def __repr__(self):
        return 'Node(serialnumber=%s, systemmac=%s, neighbors=%s)' % \
               (self.serialnumber, self.systemmac, self.neighbors)

    def add_neighbor(self, interface, peers):
        try:
            if self.neighbors.get(interface):
                raise NodeError('Interface \'%s\' already added to node' % 
                                interface)

            _neighbors = list()
            for peer in peers:
                log.debug('Creating neighbor %s:%s for interface %s',
                          peer['device'], peer['port'], interface)
                _neighbors.append(Neighbor(peer['device'],
                                           peer['port']))
            self.neighbors[interface] = _neighbors
        except KeyError as err:
            log.error('Unable to add neighbor because of KeyError: %s' 
                      % str(err))
            raise NodeError('Unable to add neighbor because of KeyError:: %s' % 
                            err)

    def add_neighbors(self, neighbors):
        for interface, peers in neighbors.items():
            self.add_neighbor(interface, peers)

    def serialize(self):
        result = {}
        for prop in ['model', 'systemmac', 'serialnumber', 'version']:
            if getattr(self, prop):
                result[prop] = getattr(self, prop)

        neighbors = {}
        if self.neighbors:
            for interface, neighbor_list in self.neighbors.items():
                serialized_neighbor_list = []
                for neighbor in neighbor_list:
                    serialized_neighbor_list.append(
                        dict(device=neighbor.device, port=neighbor.interface))
                neighbors[interface] = serialized_neighbor_list
        result['neighbors'] = neighbors
        return result


class Topology(object):

    RESERVED_VARIABLES = ['any', 'none']

    def __init__(self, **kwargs):
        self.variables = kwargs.get('variables', dict())
        self.patterns = {'globals': list(), 'nodes': dict()}

    def __repr__(self):
        return 'Topology(variables=%d, globals=%d, nodes=%d)' % \
               (len(self.variables),
                len(self.patterns['globals']),
                len(self.patterns['nodes']))

    def add_variable(self, key, value, overwrite=False):
        if key in self.RESERVED_VARIABLES:
            log.error('Variable name \'%s\' is reserved' % key)
            raise TopologyError('Variable name \'%s\' is reserved' % key)
        elif key in self.variables and not overwrite:
            log.error('Global variable \'%s\' already exists' % key)
            raise TopologyError('Global variable \'%s\' already exists' % key)

        self.variables[key] = value

    def add_variables(self, variables):
        if not hasattr(variables, 'items'):
            log.error('Missing attribute (\'items\') from %s' % variables)
            raise TopologyError('Missing attribute (\'items\') from %s' % 
                                variables)

        for key, value in variables.items():
            self.add_variable(key, value)

    def add_pattern(self, name, **kwargs):

        try:
            kwargs['node'] = kwargs.get('node')
            kwargs['definition'] = kwargs.get('definition')
            kwargs['interfaces'] = kwargs.get('interfaces', list())
            kwargs['variables'] = kwargs.get('variables', dict())

            for key in set(self.variables).difference(kwargs['variables']):
                kwargs['variables'][key] = self.variables[key]

            pattern = Pattern(name, **kwargs)

            log.info('Pattern \'%s\' parsed successfully', pattern.name)
            log.debug('%r', pattern)

            # Add pattern to topology
            if kwargs['node']:
                self.patterns['nodes'][pattern.node] = pattern
            else:
                self.patterns['globals'].append(pattern)
        except KeyError as err:
            log.error('Unable to add pattern \'%s\': %s' % (name, err))
            raise TopologyError('Unable to add pattern \'%s\': %s' % 
                                (name, err))
        except PatternError as err:
            log.warning('Failed to add pattern \'%s\': %s' % (name, err))
            raise TopologyError('Unable to add pattern \'%s\': %s' % 
                                (name, err))

    def add_patterns(self, patterns):
        try:
            for pattern in patterns:
                self.add_pattern(**pattern)
        except TypeError as err:
            log.error('Failed to add interfaces: %s' % err)
            raise TopologyError('Failed to add patterns: %s' % err)

    def is_node_pattern(self, pattern):
        #pylint: disable=R0201
        return pattern.node

    def is_global_pattern(self, pattern):
        #pylint: disable=R0201
        return not pattern.node

    def get_patterns(self):
        return self.patterns['nodes'].values() + self.patterns['globals']

    def find_patterns(self, node):
        log.info('Searching for eligible patterns for node %s' % str(node))
        pattern = self.patterns['nodes'].get(node.systemmac, None)
        if pattern:
            log.info('Eligible pattern: %s' % pattern.name)
            return [pattern]
        else:
            log.info('Eligible patterns: all global patterns')
            return self.patterns['globals']

    def match_node(self, node):
        result = list()
        for pattern in self.find_patterns(node):
            log.info('Attempting to match pattern %s', pattern.name)
            if pattern.match_node(node):
                log.info('Match for pattern %s succeeded', pattern.name)
                result.append(pattern)
            else:
                log.info('Match for pattern %s failed', pattern.name)
        return result


class Pattern(object):

    def __init__(self, name, definition=None, interfaces=None,
                 node=None, variables=None):

        self.name = name
        self.definition = definition

        self.node = node
        self.variables = variables or dict()

        self.interfaces = list()
        if interfaces:
            self.add_interfaces(interfaces)

        self.variable_substitution()

    def __repr__(self):
        return 'Pattern(name=\'%s\')' % self.name

    def variable_substitution(self):
        try:
            log.info('Checking pattern entries for variable substitution')
            for entry in self.interfaces:
                for item in entry['patterns']:
                    for attr in ['remote_device', 'remote_interface']:
                        value = getattr(item, attr)
                        if value.startswith('$'):
                            newvalue = self.variables[value[1:]]
                            setattr(item, attr, newvalue)
                    item.refresh()
            log.info('Variable substitution is complete')
        except KeyError:
            log.error('Variable substitution failed due to unknown variable')
            raise PatternError('Variable substitution failed due to '
                               'unknown variable')

    def serialize(self):
        data = dict(name=self.name, definition=self.definition)
        data['variables'] = self.variables
        data['node'] = self.node

        interfaces = []
        for item in self.interfaces:
            _item = item['metadata']
            interfaces.append({_item['interface']: _item['neighbors']})
        data['interfaces'] = interfaces

        return data

    @staticmethod
    def parse_interface(neighbor):
        try:
            if hasattr(neighbor, 'items'):
                remote_device = neighbor['device']
                remote_interface = neighbor.get('port', 'any')

            else:
                if neighbor == 'any':
                    remote_device, remote_interface = 'any', 'any'
                elif neighbor == 'none':
                    remote_device, remote_interface = 'none', 'none'
                elif ':' not in neighbor:
                    remote_device = neighbor
                    remote_interface = 'any'
                else:
                    tokens = neighbor.split(':')
                    remote_device = tokens[0]
                    remote_interface = tokens[1]

            remote_device = str(remote_device).strip()
            if len(remote_device.split()) != 1:
                log.error('Invalid peer device: %s' % remote_device)
                raise PatternError('Invalid peer device: %s' % remote_device)

            remote_interface = str(remote_interface).strip()
            if len(remote_interface.split()) != 1:
                log.error('Invalid peer interface: %s' % remote_interface)
                raise PatternError('Invalid peer interface: %s' % 
                                   remote_interface)

            return (remote_device, remote_interface)
        except KeyError as err:
            log.error('Missing required attribute from neighbor: %s' % err)
            raise PatternError('Missing required attribute from neighbor: %s' %
                               err)

    def add_interface(self, interface):
        try:
            if not hasattr(interface, 'items'):
                log.error('\'interface\' argument has no attribute \'items\'')
                raise PatternError('\'interface\' argument has no attribute '
                                   '\'items\'')

            for intf, neighbors in interface.items():
                (remote_device, remote_interface) = \
                    self.parse_interface(neighbors)

                metadata = dict(interface=intf, neighbors=neighbors)

                patterns = list()
                if intf in ['none', 'any']:
                    patterns.append(InterfacePattern(intf, remote_device, 
                                                     remote_interface))
                else:
                    for item in expand_range(intf):
                        pattern = InterfacePattern(item, remote_device, 
                                                   remote_interface)
                        patterns.append(pattern)
                self.interfaces.append(dict(metadata=metadata,
                                            patterns=patterns))
        except InterfacePatternError as exc:
            log.exception('Unable add interface pattern \'%s\': %s', 
                          (interface, exc))
            raise PatternError('Unable add interface pattern \'%s\': %s', 
                               (interface, exc))

    def add_interfaces(self, interfaces):
        try:
            for interface in interfaces:
                self.add_interface(interface)
        except TypeError as err:
            log.error('Failed to add interfaces: %s' % err)
            raise PatternError('Failed to add interfaces: %s' % err)


    def match_node(self, node):

        log.info('Attempting to match node (%s)' % str(node))

        patterns = list()
        for entry in self.interfaces:
            for pattern in entry['patterns']:
                patterns.append(pattern)

        log.info('Patterns: %s' % str(patterns))

        for interface, neighbors in node.neighbors.items():
            log.info('Attepting to match interface %s(%s)' % 
                     (interface, str(neighbors)))                

            match = False
            for index, pattern in enumerate(patterns):
                log.info('Checking pattern: %s' % pattern)
                result = pattern.match(interface, neighbors)

                # True, False, None
                if result is True:
                    log.info('Pattern %s matched successfully' %
                             pattern)
                    del patterns[index]
                    match = True
                    break
                elif result is False:
                    log.info('Failed to match node: interface %s does not '
                             'comply with %s'  % 
                             (interface, str(pattern)))
                    return False

            if not match:
                log.info('Interface %s did not match any patterns', 
                         interface)

        for pattern in patterns:
            if pattern.is_positive_constraint():
                log.warning('Pattern %s did not match any interface', 
                          pattern)
                return False
        return True


class InterfacePattern(object):

    KEYWORDS = {
        'any': RegexFunction('.*'),
        'none': RegexFunction('[^a-zA-Z0-9]')
    }

    FUNCTIONS = {
        'exact': ExactFunction,
        'includes': IncludesFunction,
        'excludes': ExcludesFunction,
        'regex': RegexFunction
    }

    def __init__(self, interface, remote_device, remote_interface):

        self.interface = interface
        self.remote_device = remote_device
        self.remote_interface = remote_interface

        self.interface_re = self.compile(interface)
        self.remote_device_re = self.compile(remote_device)
        self.remote_interface_re = self.compile(remote_interface)

    def __repr__(self):
        return 'InterfacePattern(interface=%s, remote_device=%s, ' \
               'remote_interface=%s)' % \
                (self.interface, self.remote_device, self.remote_interface)

    def refresh(self):
        self.interface_re = self.compile(self.interface)
        self.remote_device_re = self.compile(self.remote_device)
        self.remote_interface_re = self.compile(self.remote_interface)

    def compile(self, value):
        if value in self.KEYWORDS:
            return self.KEYWORDS[value]

        try:
            match = FUNC_RE.match(value)
            if match:
                function = match.group('function')
                arg = match.group('arg')
                log.debug('Found function %s with arg %s', function, arg)
                return self.FUNCTIONS[function](arg)
            else:
                return ExactFunction(value)
        except KeyError:
            log.error('Unknown function \'%s\'', function)
            raise InterfacePatternError

    def match(self, interface, neighbors):
        for neighbor in neighbors:
            res = self.match_neighbor(interface, neighbor)
            if res is True:
                return True
            elif res is False:
                return False
        return None

    def match_neighbor(self, interface, neighbor):
        # pylint: disable=R0911,R0912
        log.info('Attempting to match %s(%s) against %r' % 
                 (interface, neighbor, self))
        
        if self.interface == 'any':
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    return True
                elif self.remote_interface == 'none':
                    # bogus
                    return False
                else:
                    if self.match_remote_interface(neighbor.interface):
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
                    if self.match_remote_device(neighbor.device):
                        return True
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbor.device):
                        return False 
                else:
                    if(self.match_remote_device(neighbor.device) and
                       self.match_remote_interface(neighbor.interface)):
                        return True

        elif self.interface == 'none':
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    # bogus
                    return False
                elif self.remote_interface == 'none':
                    # bogus
                    return False
                else:
                    if self.match_remote_interface(neighbor.interface):
                        return False
            elif self.remote_device == 'none':
                if self.remote_interface == 'any':
                    # bogus
                    return False
                elif self.remote_interface == 'none':
                    # no LLDP capable neighbors
                    return False
                else:
                    # bogus
                    return False
            else:
                if self.remote_interface == 'any':
                    if self.match_remote_device(neighbor.device):
                        return False
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbor.device):
                        return False
                else:
                    if(self.match_remote_device(neighbor.device) and
                       self.match_remote_interface(neighbor.interface)):
                        return False
        else:
            if self.remote_device == 'any':
                if self.remote_interface == 'any':
                    if self.match_interface(interface):
                        return True
                elif self.remote_interface == 'none':
                    if self.match_interface(interface):
                        return False
                else:
                    if(self.match_interface(interface) and
                        self.match_remote_interface(neighbor.interface)):
                        return True
            elif self.remote_device == 'none':
                if self.remote_interface == 'any':
                    if self.match_interface(interface):
                        return False
                elif self.remote_interface == 'none':
                    if self.match_interface(interface):
                        return False
                else:
                    if(self.match_interface(interface) and
                        self.match_remote_interface(neighbor.interface)):
                        return False
            elif self.match_interface(interface):
                if self.remote_interface == 'any':
                    if self.match_remote_device(neighbor.device):
                        return True
                elif self.remote_interface == 'none':
                    if self.match_remote_device(neighbor.device):
                        return False
                else:
                    if(self.match_interface(interface) and
                       self.match_remote_device(neighbor.device) and
                       self.match_remote_interface(neighbor.interface)):
                        return True 

        return None


    def match_interface(self, interface):
        if self.interface == 'any':
            return True
        elif self.interface is None:
            return False
        else:
            return self.interface_re.match(interface)

    def match_remote_device(self, remote_device):
        if self.remote_device == 'any':
            return True
        elif self.remote_device is None:
            return False
        else:
            return self.remote_device_re.match(remote_device)

    def match_remote_interface(self, remote_interface):
        if self.interface == 'any':
            return True 
        elif self.interface is None:
            return False 
        else:
            return self.remote_interface_re.match(remote_interface)

    def is_positive_constraint(self):
        if self.interface == 'any':
            if self.remote_device == 'any':
                return True
            elif self.remote_device != 'none':
                return self.interface != 'none'

        elif self.interface != 'none':
            if self.remote_device == 'any':
                return True
            elif self.remote_device != 'none':
                return self.interface != 'none'
