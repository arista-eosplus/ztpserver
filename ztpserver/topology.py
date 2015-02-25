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
# pylint: disable=C0103,W0142
#
import collections
import logging
import os
import re
import string # pylint: disable=W0402

from ztpserver.validators import validate_neighbordb, validate_pattern
from ztpserver.resources import ResourcePool
from ztpserver.constants import CONTENT_TYPE_YAML
from ztpserver.serializers import load, SerializerError
from ztpserver.utils import expand_range, parse_interface, url_path_join
from ztpserver.config import runtime

ANY_DEVICE_PARSER_RE = re.compile(r':(?=[any])')
NONE_DEVICE_PARSER_RE = re.compile(r':(?=[none])')
FUNC_RE = re.compile(r'(?P<function>\w+)(?=\(\S+\))\([\'|\"]'
                     r'(?P<arg>.+?)[\'|\"]\)')

ALL_CHARS = set([chr(c) for c in range(256)])
NON_HEX_CHARS = ALL_CHARS - set(string.hexdigits)

log = logging.getLogger(__name__)


Neighbor = collections.namedtuple('Neighbor', ['device', 'interface'])

def neighbordb_path():
    ''' Returns the path for neighbordb based on the conf file
    '''

    filepath = runtime.default.data_root
    filename = runtime.neighbordb.filename
    return os.path.join(filepath, filename)

def load_file(filename, content_type, node_id):
    ''' Returns the contents of a file specified by filename.

    The requred content_type argument is required and indicates the
    text serialization format the contents are stored in.

    If the serializer load function encounters errors, None is returned

    '''
    try:
        return load(filename, content_type, node_id)
    except SerializerError:
        log.error('%s: failed to load file: %s' % (node_id, filename))
        raise

def load_neighbordb(node_id, contents=None):
    try:
        if not contents:
            log.info('%s: loading neighbordb file: %s' % 
                     (node_id, neighbordb_path()))
            contents = load_file(neighbordb_path(), CONTENT_TYPE_YAML,
                                 node_id)

        # neighbordb is empty
        if not contents:
            log.info('%s: unable to load neighbordb - file is missing/empty' % 
                     node_id)
            contents = dict()

        if not validate_neighbordb(contents, node_id):
            log.error('%s: failed to validate neighbordb' % node_id)
            return

        neighbordb = Neighbordb(node_id)

        if 'variables' in contents:
            neighbordb.add_variables(contents['variables'])

        if 'patterns' in contents:
            neighbordb.add_patterns(contents['patterns'])

        log.debug('%s: loaded neighbordb: %s' % (node_id, neighbordb))
        return neighbordb
    except SerializerError as err:
        # pylint: disable=E1101
        tokens = err.message.split('Error:')
        log.error('%s: failed to load neighbordb: %s' % 
                  (node_id, 
                   'Error:'.join(tokens[1:]) 
                   if len(tokens) > 1
                   else err.message))
        return None
    except Exception as err:
        log.error('%s: failed to load neighbordb because of error: %s' %
                  (node_id, err))
        return None

def load_pattern(pattern, content_type=CONTENT_TYPE_YAML, node_id=None):
    """ Returns an instance of Pattern """
    try:
        if not isinstance(pattern, collections.Mapping):
            pattern = load_file(pattern, content_type,
                                node_id)
            if 'config-handler' in pattern:
                pattern['config_handler'] = pattern['config-handler']
                del pattern['config-handler']

        # add dummy values to pass validation
        for dummy in ['definition', 'name', 'config_handler']:
            if dummy not in pattern:
                pattern[dummy] = dummy

        if not validate_pattern(pattern, node_id):
            log.error('%s: failed to validate pattern attributes' % node_id)
            return None

        pattern['node_id'] = node_id
        return Pattern(**pattern)
    except TypeError as exc:
        log.error('%s: failed to load pattern \'%s\' (%s)' % 
                  (node_id, pattern, exc))

def create_node(nodeattrs):
    try:
        if nodeattrs.get('systemmac') is not None:
            _systemmac = nodeattrs['systemmac']
            for symbol in [':', '.']:
                _systemmac = str(_systemmac).replace(symbol, '')
            nodeattrs['systemmac'] = _systemmac
        node = Node(**nodeattrs)
        log.debug('%s: created node object %r' % (node.identifier(), node))
        return node
    except KeyError as err:
        log.error('Failed to create node - missing attribute: %s' % err)

def resources(attributes, node, node_id):
    log.debug('%s: computing resources (attr=%s)' % 
              (node_id, attributes))

    _attributes = dict()
    _resources = ResourcePool(node_id)

    for key, value in attributes.items():
        if hasattr(value, 'items'):
            value = resources(value, node, node_id)
        elif hasattr(value, '__iter__'):
            _value = list()
            for item in value:
                match = FUNC_RE.match(item)
                if match:
                    method = getattr(_resources, match.group('function'))
                    _value.append(method(match.group('arg')))
                else:
                    _value.append(item)
            value = _value
        else:
            match = FUNC_RE.match(str(value))
            if match:
                method = getattr(_resources, match.group('function'))
                value = method(match.group('arg'))
        _attributes[key] = value
    log.debug('%s: resources: %s' % (node_id, _attributes))
    return _attributes

def replace_config_action(resource, filename=None):
    ''' Builds a definition with a single action replace_config '''

    filename = filename or 'startup-config'
    server_url = runtime.default.server_url
    url = url_path_join(server_url, 'nodes/', str(resource), filename)

    action = dict(name='install static startup-config file',
                  action='replace_config',
                  always_execute=True,
                  attributes={'url': url})

    return action

class NodeError(Exception):
    ''' Base exception class for :py:class:`Node` '''
    pass


class PatternError(Exception):
    ''' Base exception class for :py:class:`Pattern` '''
    pass


class InterfacePatternError(Exception):
    ''' Base exception class for :py:class:`InterfacePattern` '''
    pass


class NeighbordbError(Exception):
    ''' Base exception class for :py:class:`Neighbordb` '''
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

    def identifier(self):
        identifier = runtime.default.identifier
        return getattr(self, identifier)

    def add_neighbor(self, interface, peers):
        try:
            if self.neighbors.get(interface):
                raise NodeError('%s: interface \'%s\' already added to node' % 
                                (self.identifier(), interface))

            _neighbors = list()
            for peer in peers:
                log.debug('%s: creating neighbor %s:%s for interface %s' %
                          ( self.identifier(), peer['device'], 
                            peer['port'], interface))
                _neighbors.append(Neighbor(peer['device'],
                                           peer['port']))
            self.neighbors[interface] = _neighbors
        except KeyError as err:
            log.error('%s: failed to neighbor because of missing key (%s)' % 
                      (self.identifier(), str(err)))
            raise NodeError('%s: failed to neighbor because of KeyError (%s)' % 
                      (self.identifier(), str(err)))

    def add_neighbors(self, neighbors):
        log.info('%s: parsing node\'s LLDP Neighbor information' %
                 self.identifier())
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


class Neighbordb(object):

    RESERVED_VARIABLES = ['any', 'none']

    def __init__(self, node_id):
        self.node_id = node_id
        
        self.variables = dict()
        self.patterns = {'globals': list(), 'nodes': dict()}

    def __repr__(self):
        return 'Neighbordb(variables=%d, globals=%d, nodes=%d)' % \
               (len(self.variables),
                len(self.patterns['globals']),
                len(self.patterns['nodes']))

    def add_variable(self, key, value, overwrite=False):
        if key in self.RESERVED_VARIABLES:
            log.error('%s: failed to add variable: %s (reserved keyword)' % 
                      (self.node_id, key))
            raise NeighbordbError('%s: failed to add variable: %s '
                                '(reserved keyword)' % (self.node_id, key))
        elif key in self.variables and not overwrite:
            log.error('%s: failed to add variable: %s (duplicate)' % 
                      (self.node_id, key))
            raise NeighbordbError('%s: failed to add variable %s '
                                '(duplicate)' % (self.node_id, key))

        self.variables[key] = value

    def add_variables(self, variables):
        if not hasattr(variables, 'items'):
            log.error('%s: failed to add variables: missing attribute '
                      '\'items\' (%s)' % (self.node_id, variables))
            raise NeighbordbError('%s: failed to add variables: '
                                  'missing attribute \'items\' (%s)' % 
                                  (self.node_id, variables))

        for key, value in variables.items():
            self.add_variable(key, value)

    def add_pattern(self, name, **kwargs):

        try:
            kwargs['node_id'] = self.node_id
            kwargs['name'] = name

            kwargs['config_handler'] = kwargs.get('config-handler', 
                                                  None)
            if 'config-handler' in kwargs:
                del kwargs['config-handler']
            kwargs['interfaces'] = kwargs.get('interfaces', list())
            kwargs['variables'] = kwargs.get('variables', dict())

            for key in set(self.variables).difference(kwargs['variables']):
                kwargs['variables'][key] = self.variables[key]
                
            pattern = Pattern(**kwargs)

            log.debug('%s: pattern \'%r\' parsed successfully' % 
                      (self.node_id, pattern))

            # Add pattern to neighbordb
            if 'node' in kwargs:
                if pattern.node not in self.patterns['nodes']: 
                    self.patterns['nodes'][pattern.node] = pattern
                else:
                    log.warning('%s: pattern \'%r\' ignored because '
                                'another node-specific pattern is '
                                'configured earlier in neighbordb'
                                '\'%r\'' % 
                                (self.node_id, pattern,
                                 self.patterns['nodes'][pattern.node]))
            else:
                self.patterns['globals'].append(pattern)
        except KeyError as err:
            log.error('%s: failed to add pattern \'%s\' because of '
                      'missing key (%s)' % (self.node_id, name, str(err)))
            raise NeighbordbError('%s: failed to pattern \'%s\' because of '
                                'missing key (%s)' % 
                                  (self.node_id, name, str(err)))
        except PatternError:
            log.error('%s: failed to add pattern \'%s\'' % 
                      (self.node_id, name))
            raise NeighbordbError('%s: failed to add pattern \'%s\'' % 
                                  (self.node_id, name))

    def add_patterns(self, patterns):
        try:
            for pattern in patterns:
                self.add_pattern(**pattern)
        except TypeError as err:
            log.error('%s: failed to add patterns %s: %s' % 
                      (self.node_id, patterns, str(err)))
            raise NeighbordbError('%s: failed to add patterns %s: %s' %
                                  (self.node_id, patterns, str(err)))

    def is_node_pattern(self, pattern):
        #pylint: disable=R0201
        return pattern.node

    def is_global_pattern(self, pattern):
        #pylint: disable=R0201
        return not pattern.node

    def get_patterns(self):
        return self.patterns['nodes'].values() + self.patterns['globals']

    @staticmethod
    def identifier(node):
        identifier = runtime.default.identifier
        return node[identifier]
        
    def find_patterns(self, node):
        identifier = node.identifier()
        log.debug('%s: searching for eligible patterns' % 
                  identifier)

        result = []

        pattern = self.patterns['nodes'].get(identifier, None)
        if pattern:
            log.debug('%s: node-specific pattern eligible in neighbordb: %s' %
                      (identifier, 
                       pattern.name))
            result += [pattern]

        elif self.patterns['globals']:
            log.debug('%s: global patterns eligible in neighbordb' %
                      identifier)
            result += self.patterns['globals']
        else:
            log.debug('%s: no patterns eligible in neighbordb' %
                      identifier)

        return result

    def match_node(self, node):
        identifier = node.identifier()
        result = list()
        for pattern in self.find_patterns(node):
            log.debug('%s: attempting to match pattern %s' % 
                      (identifier, pattern.name))
            if pattern.match_node(node):
                log.debug('%s: pattern %s matched' % 
                          (identifier, pattern.name))
                result.append(pattern)
            else:
                log.debug('%s: pattern %s match failed' % 
                          (identifier, pattern.name))
        return result


class Pattern(object):

    def __init__(self, name=None, definition=None, 
                 config_handler=None, interfaces=None,
                 node=None, variables=None, node_id=None):

        self.name = name
        self.definition = definition
        self.config_handler = config_handler

        self.node = node
        self.node_id = node_id
        self.variables = variables or dict()

        self.interfaces = list()
        if interfaces:
            self.add_interfaces(interfaces)

        self.variable_substitution()

    def __repr__(self):
        return 'Pattern(name=\'%s\')' % self.name

    def variable_substitution(self):
        try:
            log.debug('%s: checking pattern \'%s\' entries for variable '
                      'substitution' % (self.node_id, self.name))
            for entry in self.interfaces:
                for item in entry['patterns']:
                    for attr in ['remote_device', 'remote_interface']:
                        value = getattr(item, attr)
                        if value.startswith('$'):
                            newvalue = self.variables[value[1:]]
                            setattr(item, attr, newvalue)
                    item.refresh()
            log.debug('%s: pattern \'%s\' variable substitution complete' %
                      (self.node_id, self.name))
        except KeyError as exc:
            log.debug('%s: pattern \'%s\' variable substitution failed: %s' %
                      (self.node_id, self.name, str(exc)))
            raise PatternError('%s: pattern \'%s\' variable substitution '
                               'failed: %s' % 
                               (self.node_id, self.name, str(exc)))

    def serialize(self):
        data = dict(name=self.name, definition=self.definition,
                    variables=self.variables, node=self.node)

        data['config-handler'] = self.config_handler

        interfaces = []
        for item in self.interfaces:
            _item = item['metadata']
            interfaces.append({_item['interface']: _item['neighbors']})
        data['interfaces'] = interfaces

        return data

    def parse_interface(self, neighbor):
        try:
            return parse_interface(neighbor, self.node_id)
        except Exception as err:
            raise PatternError(str(err))

    def add_interface(self, interface):
        try:
            if not hasattr(interface, 'items'):
                log.error('%s: pattern \'%s\' - failed to add interface %s: '
                          'missing attribute (items)' %
                          (self.node_id, self.name, interface))
                raise PatternError('%s: pattern \'%s\' - failed to add '
                                   'interface %s: missing attribute (items)' %
                                   (self.node_id, self.name, interface))

            for intf, neighbors in interface.items():
                (remote_device, remote_interface) = \
                    self.parse_interface(neighbors)

                metadata = dict(interface=intf, neighbors=neighbors)

                patterns = list()
                if intf in ['none', 'any']:
                    patterns.append(InterfacePattern(intf, remote_device, 
                                                     remote_interface, 
                                                     self.node_id))
                else:
                    for item in expand_range(intf):
                        pattern = InterfacePattern(item, remote_device, 
                                                   remote_interface,
                                                   self.node_id)
                        patterns.append(pattern)
                self.interfaces.append(dict(metadata=metadata,
                                            patterns=patterns))
        except InterfacePatternError:
            log.error('%s: pattern \'%s\' - failed to add interface %s' %
                      (self.node_id, self.name, interface))
            raise PatternError('%s: pattern \'%s\' - failed to add '
                               'interface %s' %
                               (self.node_id, self.name, interface))

    def add_interfaces(self, interfaces):
        try:
            for interface in interfaces:
                self.add_interface(interface)
        except TypeError as err:
            log.error('%s: pattern \'%s\' - failed to add interfaces %s: %s' %
                      (self.node_id, self.name, interface, str(err)))
            raise PatternError('%s: pattern \'%s\' - failed to add '
                               'interfaces %s: %s' %
                               (self.node_id, self.name, interface, str(err)))

    def match_node(self, node):

        log.debug('%s: pattern \'%s\' - attempting to match node (%r)' % 
                  (self.node_id, self.name, str(node)))

        # No need to match system ID - that it already taken care of
        # while selecting the set of nodes which are eligible for a 
        # match.

        patterns = list()
        for entry in self.interfaces:
            for pattern in entry['patterns']:
                patterns.append(pattern)

        for interface, neighbors in node.neighbors.items():
            log.debug('%s: pattern \'%s\' - attempting to match '
                      'interface %s(%s)' %
                      (self.node_id, self.name, interface, str(neighbors)))

            match = False
            for index, pattern in enumerate(patterns):
                log.debug('%s: pattern \'%s\' - checking interface pattern '
                          'for %s: %s' % 
                          (self.node_id, self.name, interface, pattern))
                result = pattern.match(interface, neighbors)

                # True, False, None
                if result is True:
                    log.debug('%s: pattern \'%s\' - interface pattern match '
                              'for %s: %s' % 
                              (self.node_id, self.name, interface, pattern))
                    del patterns[index]
                    match = True
                    break
                elif result is False:
                    log.debug('%s: pattern \'%s\' - interface pattern match '
                              'failure for %s: %s' % 
                              (self.node_id, self.name, interface, pattern))
                    return False

            if not match:
                log.debug('%s: pattern \'%s\' - interface %s did not match '
                          'any interface patterns' % 
                          (self.node_id, self.name, interface))

        for pattern in patterns:
            if pattern.is_positive_constraint():
                log.debug('%s: pattern \'%s\' - interface pattern %s did '
                          'not match any interface' % 
                          (self.node_id, self.name, pattern))
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

    def __init__(self, interface, remote_device, remote_interface, node_id):

        match = re.match(r'^[ehnrtE]+(\d.*)$', interface)
        if match:
            self.interface = 'Ethernet%s' % match.groups()[0]
        else:
            self.interface = interface

        self.remote_device = remote_device
        self.remote_interface = remote_interface
        self.node_id = node_id

        self.remote_device_re = self.compile(remote_device)
        self.remote_interface_re = self.compile(remote_interface)

    def __repr__(self):
        return 'InterfacePattern(interface=%s, remote_device=%s, ' \
               'remote_interface=%s)' % \
                (self.interface, self.remote_device, self.remote_interface)

    def refresh(self):
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
                return self.FUNCTIONS[function](arg)
            else:
                return ExactFunction(value)
        except KeyError as exc:
            log.error('%s: compile error: unknown function \'%s\' (%s)' % 
                      (self.node_id, function, str(exc)))
            raise InterfacePatternError

    def match(self, interface, neighbors):
        for neighbor in neighbors:
            res = self.match_neighbor(interface, Neighbor(neighbor.device,
                                                          neighbor.interface))
            if res is True:
                return True
            elif res is False:
                return False
        return None

    def match_neighbor(self, interface, neighbor):
        # pylint: disable=R0911,R0912
        log.debug('%s: attempting to match %s(%s) against '
                  'interface pattern %r' % 
                  (self.node_id, interface, neighbor, self))
        
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
            return self.interface == interface

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
