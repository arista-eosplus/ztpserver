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

import string
import re
import inspect
import logging

from ztpserver.topology import Pattern, PatternError
from ztpserver.utils import expand_range

REQUIRED_PATTERN_ATTRIBUTES = ['name', 'definition', 'interfaces']
INTERFACE_PATTERN_KEYWORDS = ['any', 'none']
ANTINODE_PATTERN = r'[^%s]' % string.hexdigits
VALID_INTERFACE_RE = re.compile(r'^Ethernet[1-9]\d*(?:\/\d+){0,2}$')
KW_ANY_RE = re.compile(r'[any]')
KW_NONE_RE = re.compile(r'[none]')
WC_PORT_RE = re.compile(r'.*')

INVALID_INTERFACE_PATTERNS = [(KW_ANY_RE, KW_ANY_RE, KW_NONE_RE),
                              (KW_ANY_RE, KW_NONE_RE, KW_NONE_RE),
                              (KW_ANY_RE, KW_NONE_RE, KW_ANY_RE),
                              (KW_ANY_RE, KW_NONE_RE, WC_PORT_RE),
                              (KW_NONE_RE, KW_ANY_RE, KW_ANY_RE),
                              (KW_NONE_RE, KW_ANY_RE, KW_NONE_RE),
                              (KW_NONE_RE, KW_NONE_RE, KW_ANY_RE),
                              (KW_NONE_RE, KW_NONE_RE, KW_NONE_RE),
                              (KW_NONE_RE, KW_NONE_RE, WC_PORT_RE)]


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
                raise ValidationError('invalid global variables value')

    def validate_patterns(self):
        if not self.data.get('patterns'):
            raise ValidationError('missing required \'patterns\' attribute')


        for index, entry in enumerate(self.data.get('patterns')):
            try:
                name = entry.get('name')
                hash(name)
            except TypeError:
                name = str(name)

            validator = PatternValidator()

            if validator.validate(entry):
                log.info('Add pattern %s to valid patterns', name)
                self.valid_patterns.add((index, name))
            else:
                log.info('Add pattern %s to failed patterns', name)
                self.error('Unable to validate pattern %s (%d)', name, index)
                self.failed_patterns.add((index, name))


class PatternValidator(Validator):

    def __init__(self):
        self.failed_interface_patterns = set()
        self.passed_interface_patterns = set()
        super(PatternValidator, self).__init__()

    def validate_name(self):
        if 'name' not in self.data:
            raise ValidationError('missing required attribute \'name\'')

        if self.data is None or self.data['name'] is None:
            raise ValidationError('name attribute cannot be none')

        if hasattr(self.data['name'], '__iter__'):
            raise ValidationError('name attribute cannot be iterable')

    def validate_interfaces(self):
        if 'interfaces' not in self.data:
            raise ValidationError('missing required attribute \'interfaces\'')

        if not hasattr(self.data['interfaces'], '__iter__'):
            raise ValidationError('interface attribute is not iterable')

        for index, pattern in enumerate(self.data['interfaces']):
            if not hasattr(pattern, 'items'):
                raise ValidationError('invalid value for interfaces')

            validator = InterfacePatternValidator()
            if validator.validate(pattern):
                log.info('Interface pattern at index %d passed', index)
                self.passed_interface_patterns.add((index, repr(pattern)))
            else:
                self.error('Interface pattern at index %d failed', index)
                self.failed_interface_patterns.add((index, repr(pattern)))

    def validate_definition(self):
        if 'definition' not in self.data:
            raise ValidationError('missing required attribute \'definition\'')

        if self.data is None or self.data['definition'] is None:
            raise ValidationError('definition attribute cannot be none')

        if hasattr(self.data['definition'], '__iter__'):
            raise ValidationError('definition attribute cannot be iterable')

        for wspc in string.whitespace:
            if wspc in self.data['definition']:
                raise ValidationError('whitespace not allowed in definition')

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
            # todo: make this check more intelligent
            node = str(node).replace(':', '').replace('.', '')
            if re.search(ANTINODE_PATTERN, str(node)) or len(node) != 12:
                raise ValidationError('invalid node attribute')

    def validate_variables(self):
        if 'variables' in self.data:
            if not hasattr(self.data['variables'], '__iter__'):
                raise ValidationError('variable attribute is not iterable')


class InterfacePatternValidator(Validator):

    def validate_interface_pattern(self):

        for interface, peer in self.data.items():
            if peer is None:
                raise ValidationError('invalid peer')

        try:
            (intf, device, port) = Pattern.parse_interface(interface, peer)
        except PatternError:
            raise ValidationError('Validation failed due to PatternError')

        if not VALID_INTERFACE_RE.match(interface):
            if interface not in INTERFACE_PATTERN_KEYWORDS:
                try:
                    expand_range(interface)
                except Exception:
                    raise ValidationError('invalid interface name: %s' % intf)

        try:
            for entry in expand_range(intf):
                self._validate_pattern(entry, device, port)
        except TypeError:
            self._validate_pattern(intf, device, port)

    def _validate_pattern(self, interface, device, port):
        for interface_re, device_re, port_re in INVALID_INTERFACE_PATTERNS:
            if interface_re.match(interface) and device_re.match(device) \
               and port_re.match(port):
                raise ValidationError('invalid interface pattern found')

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

