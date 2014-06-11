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
VALID_INTERFACE_RE = re.compile(r'^Ethernet\d+(?:\/\d+){0,2}$')
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


log = logging.getLogger(__name__)


class Validator(object):

    def __init__(self):
        self.contents = None
        self.errors = False
        self.messages = list()

    def validate(self, content):
        self.contents = content
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name in methods:
            if name[0].startswith('validate_'):
              method = getattr(self, name[0])
              method()
        return not self.errors

    def error(self, msg, *args, **kwargs):
        try:
            log.error(msg, *args)
            self.messages.append(msg % args)
            self.errors = True
        except Exception:
            log.exception('Unknown error occurred trying to execute \'error\'')
            raise

class TopologyValidator(Validator):

    def __init__(self):
        self.failed_patterns = set()
        self.valid_patterns = set()
        super(TopologyValidator, self).__init__()

    def validate_variables(self):
        variables = self.contents.get('variables')
        if variables:
            if not hasattr(variables, '__iter__'):
                self.error('Validation failed because global variables format')

    def validate_patterns(self):
        patterns = self.contents.get('patterns')
        if not patterns:
            self.error('Validation failed due to missing \'patterns\' '
                       'attribute')

        validator = PatternValidator()
        for index, entry in enumerate(patterns):
            if not validator.validate(entry):
                log.info('Add pattern %s to failed patterns', entry.get('name'))
                self.error('Unable to validate pattern at index %d', index)
                try:
                    self.failed_patterns.add((index, entry.get('name')))
                except TypeError:
                    self.failed_patterns.add((index, None))
                for msg in validator.messages:
                    self.messages.append(msg)
            else:
                log.info('Adding pattern %s to valid patterns', entry.get('name'))
                self.valid_patterns.add((index, entry.get('name')))

class PatternValidator(Validator):

    def validate_pattern(self):
        if self.contents.get('name') is None:
            self.error('Validation failed due to missing name attribute')

        if not set(REQUIRED_PATTERN_ATTRIBUTES).issubset(self.contents.keys()):
            self.error('Validation failed due to missing attributes')

        if 'definition' in self.contents:
            self._validate_definition(self.contents['definition'])

        if 'node' in self.contents:
            self._validate_node(self.contents['node'])

        if 'variables' in self.contents:
            self._validate_pattern_variables(self.contents['variables'])

        if 'interfaces' in self.contents:
            if not hasattr(self.contents['interfaces'], '__iter__'):
                self.error('Validation failed due to interfaces attribute is '
                           'not iterable')

            for item in self.contents['interfaces']:
                if not hasattr(item, 'items'):
                    self.error('Validation failed due to invalid interface '
                               'pattern %s', item)
                    break

                for interface, peer in item.items():
                    if peer is None:
                        self.error('Validation failed due to invalid peer')
                        break

                    try:
                        (interface, device, port) = \
                            Pattern.parse_interface(interface, peer)
                    except PatternError:
                        self.error('Validation failed due to PatternError')
                    else:
                        try:
                            for entry in expand_range(interface):
                                self._validate_pattern(entry, device, port)
                        except TypeError:
                            self._validate_pattern(interface, device, port)

    def _validate_definition(self, definition):
        try:
            if definition is None or hasattr(definition, '__iter__'):
                raise Exception('Validation failed due to invalid '
                                '\'definition\' attribute')
            for ws in string.whitespace:
                if ws in definition:
                    raise Exception('Validation failed due to invalid '
                                    '\'definition\' attribute')
        except Exception as exc:
            self.error(exc.message)
            return False
        else:
            return True

    def _validate_pattern_variables(self, variables):
        try:
            if not hasattr(variables, '__iter__'):
                raise Exception('Failed to parse pattern because pattern '
                                'variables are not iterable')
        except Exception as exc:
            self.error(exc.message)
            return False
        else:
            return True

    def _validate_node(self, node):
        try:
            if re.search(ANTINODE_PATTERN, str(node)) or len(node) != 12:
                raise Exception('Validation failed due to invalid \'node\' '
                                'attribute')
        except Exception as exc:
            self.error(exc.message)
            return False
        else:
            return True

    def _validate_pattern(self, interface, device, port):
        if interface not in INTERFACE_PATTERN_KEYWORDS and \
           not VALID_INTERFACE_RE.match(interface):
            self.error('Failed to parse pattern due to invalid interface '
                       'name %s', interface)
            return False

        pattern_failed = False
        for interface_re, device_re, port_re in INVALID_INTERFACE_PATTERNS:
            if interface_re.match(interface) and device_re.match(device) \
               and port_re.match(port):
                self.error('Failed to parse pattern (%s, %s, %s) due to invalid'
                           ' interface pattern', interface, device, port)
                pattern_failed = True
        return not pattern_failed


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

