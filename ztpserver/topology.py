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


Neighbor = collections.namedtuple('Neighbor', ['device', 'port'])


class Node(object):
    ''' A Node object is maps the metadata from an EOS node.  It provides
    access to the node's meta data including interfaces and the
    associated neighbors found on those interfaces.
    '''

    def __init__(self, systemmac, **kwargs):
        self.systemmac = str(systemmac)
        self.model = str(kwargs.get('model', ''))
        self.serialnumber = str(kwargs.get('serialnumber', ''))
        self.version = str(kwargs.get('version', ''))

        self.neighbors = OrderedCollection()
        if 'neighbors' in kwargs:
            self.add_neighbors(kwargs['neighbors'])

    def __repr__(self):
        return 'Node(serialnumber=%s, systemmac=%s)' % \
               (self.serialnumber, self.systemmac)

    def add_neighbor(self, interface, peers):
        try:
            if self.neighbors.get(interface):
                raise NodeError('interface \'%s\' already exists' % interface)
            _neighbors = list()
            for peer in peers:
                log.debug('Creating neighbor %s:%s for interface %s',
                          peer['device'], peer['port'], interface)
                _neighbors.append(Neighbor(peer['device'],
                                           peer['port']))
            self.neighbors[interface] = _neighbors
        except KeyError:
            log.error('Unable to add neighbor due to missing attribute')
            raise NodeError('missing required attribute')

    def add_neighbors(self, neighbors):
        try:
            for interface, peers in neighbors.items():
                self.add_neighbor(interface, peers)
        except AttributeError:
            log.error('Unable to add neighbors due to missing attribute')
            raise NodeError('missing required attribute')

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
                        dict(device=neighbor.device, port=neighbor.port))
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
        try:
            if key in self.RESERVED_VARIABLES:
                log.error('Variable name \'%s\' is reserved', key)
                raise TopologyError
            elif key in self.variables and not overwrite:
                log.error('Global variable \'%s\' already exists', key)
                raise TopologyError
            self.variables[key] = value
        except TopologyError:
            raise

    def add_variables(self, variables):
        if not hasattr(variables, 'items'):
            log.error('Unable to process variables')
            raise TopologyError

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
            if kwargs['node'] is not None:
                self.patterns['nodes'][pattern.node] = pattern
            else:
                self.patterns['globals'].append(pattern)
        except KeyError:
            log.error('Unable to add pattern \'%s\' due to missing attributes',
                      pattern.get('name'))
            raise TopologyError
        except PatternError:
            log.warning('Failed to add pattern \'%s\' to topology', name)
            raise TopologyError
        except Exception:
            log.exception('Unexpected exception during add_pattern')
            raise TopologyError

    def add_patterns(self, patterns, continue_on_error=True):
        for pattern in patterns:
            try:
                log.debug('Adding pattern \'%s\' to topology', pattern['name'])
                self.add_pattern(**pattern)
            except TopologyError:
                if not continue_on_error:
                    raise
                continue

    def isnodepattern(self, pattern):
        #pylint: disable=R0201
        return pattern.node is not None

    def isglobalpattern(self, pattern):
        #pylint: disable=R0201
        return pattern.node == '' or pattern.node is None

    def get_patterns(self, predicate=None):
        _patterns = self.patterns['nodes'].values() + self.patterns['globals']
        return [pattern for pattern in _patterns if predicate(pattern)]
        #return filter(predicate, _patterns) if predicate else _patterns

    def find_patterns(self, node):
        try:
            systemmac = node.systemmac
            log.info('Searching for eligible patterns for node %s', systemmac)
            pattern = self.patterns['nodes'][systemmac]
            log.info('Eligible pattern: %s', pattern.name)
            return [pattern]
        except KeyError:
            log.info('Eligible patterns: all global patterns')
            return self.get_patterns(predicate=self.isglobalpattern)

    def match_node(self, node):
        try:
            result = list()
            for pattern in self.find_patterns(node):
                log.info('Attempting to match pattern %s', pattern.name)
                if pattern.match_node(node):
                    log.info('Match for pattern %s succeeded', pattern.name)
                    result.append(pattern)
                else:
                    log.info('Match for pattern %s failed', pattern.name)
            return result
        except Exception:
            log.exception('Unexpected error trying to execute match_node')
            raise TopologyError


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
                    for attr in ['device', 'port']:
                        value = getattr(item, attr)
                        if value.startswith('$'):
                            newvalue = self.variables[value[1:]]
                            setattr(item, attr, newvalue)
                    item.refresh()
            log.info('Variable substitution is complete')
        except KeyError:
            log.error('Variable substitution failed due to unknown variable')
            raise PatternError

    def serialize(self):
        try:
            data = dict(name=self.name, definition=self.definition)
            data['variables'] = self.variables
            data['node'] = self.node

            interfaces = []
            for item in self.interfaces:
                _item = item['metadata']
                interfaces.append({_item['interface']: _item['neighbors']})
            data['interfaces'] = interfaces

            return data
        except Exception:
            log.exception('Unexpected error trying to serialize object')
            raise PatternError

    def add_interface(self, interface):
        try:
            if not hasattr(interface, 'items'):
                log.error('\'interface\' argument has no attribute \'items\'')
                raise PatternError

            for key, value in interface.items():
                (interface, device, port) = self.parse_interface(key, value)

                metadata = dict(interface=interface, neighbors=value)
                if interface in ['none', 'any']:
                    patterns = [InterfacePattern(interface, device, port)]
                else:
                    patterns = list()
                    for item in expand_range(interface):
                        pattern = InterfacePattern(item, device, port)
                        patterns.append(pattern)
                self.interfaces.append(dict(metadata=metadata,
                                            patterns=patterns))

        except ValueError:
            log.error('Unable to parse interface \'%s\'', key)
            raise PatternError
        except InterfacePatternError:
            log.exception('Unable add interface pattern \'%s\'', key)
            raise PatternError
        except Exception:
            log.exception('Unexpected error trying to execute add_interface')
            raise PatternError

    def add_interfaces(self, interfaces, continue_on_error=False):
        try:
            for interface in interfaces:
                try:
                    self.add_interface(interface)
                except PatternError:
                    log.error('Unable to add interface to pattern')
                    if not continue_on_error:
                        raise
                    continue
        except TypeError:
            log.error('\'interfaces\' is not iterable')
            raise PatternError

    @staticmethod
    def parse_interface(interface, neighbor):
        try:
            if hasattr(neighbor, 'items'):
                device = neighbor['device']
                port = neighbor.get('port', 'any')

            else:
                if neighbor == 'any':
                    device, port = 'any', 'any'
                elif neighbor == 'none':
                    device, port = 'none', 'none'
                elif ':' not in neighbor:
                    device = neighbor
                    port = 'any'
                else:
                    tokens = neighbor.split(':')
                    device = tokens[0]
                    port = tokens[1]

            device = str(device).strip()
            if len(device.split()) != 1:
                log.error('Invalid peer device')
                raise PatternError

            port = str(port).strip()
            if len(port.split()) != 1:
                log.error('Invalid peer port')
                raise PatternError

            return (interface, device, port)
        except KeyError:
            log.error('Missing required attribute from neighbor')
            raise PatternError

    def match_node(self, node):

        log.info('Attempting to match node %s', node.systemmac)

        try:
            patterns = list()
            for entry in self.interfaces:
                for pattern in entry['patterns']:
                    patterns.append(pattern)
            matches = list()

            for interface, neighbors in node.neighbors.items():
                matched_index = None
                for index, pattern in enumerate(patterns):
                    try:
                        if pattern.match(interface, neighbors):
                            matched_index = index
                            break
                    except InterfacePatternError:
                        log.warning('Interface %s matched but neighbors were '
                                    'invalid', interface)
                        return False

                if matched_index is not None:
                    log.debug('Removing pattern %r from available patterns',
                              patterns[matched_index])
                    matches.append(patterns[matched_index])
                    del patterns[matched_index]
                if matched_index is None:
                    log.warning('Pattern was not matched')

            for pattern in patterns:
                log.debug('Checking remaining patterns for positive contraint')
                if not pattern.is_wildcard():
                    log.debug('pattern %s has positive contraint', pattern)
                    return False
            return True

        except Exception:
            log.exception('Unexpected exception during match_node')
            raise PatternError


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

    def __init__(self, interface, device, port):

        self.interface = interface
        self.device = device
        self.port = port

        self.interface_re = self.compile(interface)
        self.device_re = self.compile(device)
        self.port_re = self.compile(port)

    def __repr__(self):
        return 'InterfacePattern(interface=%s, device=%s, port=%s)' % \
                (self.interface, self.device, self.port)

    def refresh(self):
        self.interface_re = self.compile(self.interface)
        self.device_re = self.compile(self.device)
        self.port_re = self.compile(self.port)

    def match(self, interface, neighbors):
        log.debug('%r', self)
        log.debug('match interface: %s, neighbors: %s', interface, neighbors)

        match_interface = self.match_interface(interface)
        log.debug('match_interface=%s', match_interface)

        if match_interface in [True, None]:
            match_neighbors = self.match_neighbors(neighbors)
            log.debug('match_neighbors=%s', match_neighbors)
        else:
            log.debug('skipping match_neighbors due to match interface failure')
            match_neighbors = False

        if match_interface and not match_neighbors:
            log.warning('Interface matches but neighbors are invalid')
            raise InterfacePatternError

        return match_interface and match_neighbors

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

    def match_neighbors(self, neighbors):
        for neighbor in neighbors:
            if self.match_neighbor(neighbor):
                return True
        return False

    def match_neighbor(self, neighbor):
        match_device = self.device_re.match(neighbor.device)
        match_port = self.port_re.match(neighbor.port)
        return match_device and match_port or False

    def match_interface(self, interface):
        if self.interface == 'none':
            return None
        match = self.interface_re.match(interface)
        return match is not None and match is not False

    def is_positive_constraint(self):
        if self.interface == 'any':
            if self.device == 'any':
                return True
            elif self.device != 'none':
                return self.interface != 'none'

        elif self.interface != 'none':
            if self.device == 'any':
                return True
            elif self.device != 'none':
                return self.interface != 'none'

        return False

    def is_wildcard(self):
        return self.interface in ['any', 'none'] or \
               self.device in ['any', 'none']








