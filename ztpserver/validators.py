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
# pylint: disable=W0631

import string    #pylint: disable=W0402
import re
import inspect
import logging
import collections

from ztpserver.topology import Pattern, PatternError
from ztpserver.utils import expand_range

REQUIRED_PATTERN_ATTRIBUTES = ['name']
OPTIONAL_PATTERN_ATTRIBUTES = ['definition', 'interfaces', 'node', 'variables']
INTERFACE_PATTERN_KEYWORDS = ['any', 'none']
ANTINODE_PATTERN = r'[^%s]' % string.hexdigits
VALID_INTERFACE_RE = re.compile(r'^Ethernet[1-9]\d*(?:\/\d+){0,2}$')
KW_ANY_RE = re.compile(r' *any *')
KW_NONE_RE = re.compile(r' *none *')
WC_PORT_RE = re.compile(r'.*')


INVALID_INTERFACE_PATTERNS = [(KW_ANY_RE, KW_ANY_RE, KW_NONE_RE),
                              (KW_ANY_RE, KW_NONE_RE, KW_NONE_RE),
                              (KW_ANY_RE, KW_NONE_RE, KW_ANY_RE),
                              (KW_ANY_RE, KW_NONE_RE, WC_PORT_RE),
                              (KW_NONE_RE, KW_ANY_RE, KW_ANY_RE),
                              (KW_NONE_RE, KW_ANY_RE, KW_NONE_RE),
                              (KW_NONE_RE, KW_NONE_RE, WC_PORT_RE),
                              (KW_NONE_RE, KW_NONE_RE, KW_ANY_RE)]


log = logging.getLogger(__name__)   #pylint: disable=C0103

class ValidationError(Exception):
    ''' Base error class for validation failures '''
    pass

class Validator(object):

    def __init__(self):
        self.data = None
        self.fail = False
        self.errors = list()

    def validate(self, data):
        self.data = data
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name in methods:
            if name[0].startswith('validate_'):
                try:
                    getattr(self, name[0])()
                except ValidationError as exc:
                    cls = str(self.__class__).split('\'')[1].split('.')[-1]
                    log.info('%s validation error: %s' % (cls, exc))
                    self.error(exc)
        return not self.fail

    def error(self, msg, *args, **kwargs):
        #pylint: disable=W0613
        log.error(msg, *args)
        self.fail = True

class TopologyValidator(Validator):

    def __init__(self):
        self.failed_patterns = set()
        self.valid_patterns = set()
        super(TopologyValidator, self).__init__()

    def validate_variables(self):
        variables = self.data.get('variables')
        if variables is not None:
            if not hasattr(variables, '__iter__'):
                raise ValidationError('Invalid global variables value (%s)' %
                                      variables)

    def validate_patterns(self):
        if not self.data.get('patterns'):
            raise ValidationError('Missing required \'patterns\' attribute')

        for index, entry in enumerate(self.data.get('patterns')):
            name = str(entry.get('name'))

            validator = PatternValidator()

            if validator.validate(entry):
                log.info('Add pattern %s to valid patterns', name)
                self.valid_patterns.add((index, name))
            else:
                log.info('Unable to validate pattern %s (%d)' % (name, index))
                self.error('Unable to validate pattern %s (%d)' % (name, index))
                self.failed_patterns.add((index, name))

class PatternValidator(Validator):

    def __init__(self):
        self.failed_interface_patterns = set()
        self.passed_interface_patterns = set()
        super(PatternValidator, self).__init__()

    def validate_attributes(self):
        for attr in REQUIRED_PATTERN_ATTRIBUTES:
            if attr not in self.data:
                raise ValidationError('Missing required attribute: %s' % attr)

        for attr in OPTIONAL_PATTERN_ATTRIBUTES:
            if attr not in self.data:
                log.warning('Pattern missing optional attribute: %s', attr)

    def validate_name(self):
        if 'name' not in self.data:
            raise ValidationError('Name attribute missing')

        if self.data is None or self.data['name'] is None:
            raise ValidationError('Name attribute cannot be none')

        if not isinstance(self.data['name'], (int, basestring)):
            raise ValidationError('Name attribute must be a string')

    def validate_interfaces(self):
        if 'interfaces' not in self.data:
            return

        if not isinstance(self.data['interfaces'], collections.Iterable):
            raise ValidationError('Interface attribute is not iterable')

        for index, pattern in enumerate(self.data['interfaces']):
            if not isinstance(pattern, collections.Mapping):
                raise ValidationError('Invalid value for interfaces (%s)' %
                                      pattern)

            validator = InterfacePatternValidator()

            if validator.validate(pattern):
                log.info('Interface pattern %s passed validation', 
                         repr(pattern))
                self.passed_interface_patterns.add((index, repr(pattern)))
            else:
                log.info('Interface pattern %s failed validation', 
                         repr(pattern))
                self.failed_interface_patterns.add((index, repr(pattern)))
                raise ValidationError('Interface pattern %s failed validation', 
                                      repr(pattern))

    def validate_definition(self):
        if 'definition' not in self.data:
            return

        if self.data is None or self.data['definition'] is None:
            raise ValidationError('Definition attribute cannot be none')

        if not isinstance(self.data['definition'], basestring):
            raise ValidationError('Definition attribute must be a string')

        for wspc in string.whitespace:
            if wspc in self.data['definition']:
                raise ValidationError('Whitespace not allowed in definition')

    def validate_pattern(self):
        name = self.data.get('name')

        if name is None:
            self.error('Pattern validation failed due to missing '
                       '\'name\' attribute')

        if not set(REQUIRED_PATTERN_ATTRIBUTES).issubset(self.data.keys()):
            self.error('Pattern validation failed due to missing one or more '
                       'required attributes')

    def validate_node(self):
        node = self.data.get('node')
        if node is not None:
            node = str(node).replace(':', '').replace('.', '')
            if re.search(ANTINODE_PATTERN, str(node)) or len(node) != 12:
                raise ValidationError('Invalid node attribute (%s)' % node)

    def validate_variables(self):
        if 'variables' in self.data:
            if not hasattr(self.data['variables'], '__iter__'):
                raise ValidationError('variable attribute is not iterable')


class InterfacePatternValidator(Validator):

    def validate_interface_pattern(self):

        for interface, peer in self.data.items():
            if peer is None:
                raise ValidationError('Missing peer')

            try:
                (device, port) = Pattern.parse_interface(peer)
            except PatternError as err:
                raise ValidationError('Validation failed due to '
                                      'PatternError (%s)' % err)

            if not VALID_INTERFACE_RE.match(interface):
                if interface not in INTERFACE_PATTERN_KEYWORDS:
                    try:
                        expand_range(interface)
                    except Exception:
                        raise ValidationError('Invalid interface name (%s)' % 
                                              interface)

            try:
                for entry in expand_range(interface):
                    self._validate_pattern(entry, device, port)
            except TypeError:
                self._validate_pattern(interface, device, port)

    def _validate_pattern(self, interface, device, port):
        # pylint: disable=R0201
        if KW_NONE_RE.match(interface) and KW_NONE_RE.match(device) \
                and KW_NONE_RE.match(port):
            # no LLDP neighbors
            return

        for interface_re, device_re, port_re in INVALID_INTERFACE_PATTERNS:
            if interface_re.match(interface) and device_re.match(device) \
               and port_re.match(port):
                raise ValidationError('Invalid interface pattern: (%s, %s, %s) '
                                      'matches (%s, %s, %s)'%
                                      (interface, device, port,
                                       interface_re.pattern, 
                                       device_re.pattern, 
                                       port_re.pattern))


def _validator(contents, cls):
    try:
        validator = cls()
        result = validator.validate(contents)
        if result:
            log.info('Validation was successful')
        else:
            log.info('Validation failed')
        return result
    except Exception:
        log.exception('Unrecoverable error occured trying to run validator')
        raise

def validate_topology(contents):
    return _validator(contents, TopologyValidator)

def validate_pattern(contents):
    return _validator(contents, PatternValidator)

