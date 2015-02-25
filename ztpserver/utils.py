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
# pylint: disable=C0103

import logging
import re
import os

from urlparse import urlsplit, urlunsplit

log = logging.getLogger(__name__)

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

ETHERNET_RE = re.compile(r'^(e(t(h(ernet)?)?)?)(\d+)(\/(\d+)){0,2}$')
MANAGEMENT_RE = re.compile(r'^(m(a(nagement)?)?)(\d+)(\/(\d+)){0,2}$')
INTERFACE_NO_RE = re.compile(r'^(\d+)(\/(\d+)){0,2}$')
def expand_range(interfaces):
    ''' Returns a naturally sorted list of items expanded from interfaces. '''

    # pylint: disable=R0914,R0912
    
    items = set()
    prefix = None
    for group in [x.strip() for x in interfaces.split(',')]:
        ranges = [x.strip() for x in group.split('-')]
        if len(ranges) == 1:
            interface = ranges[0].lower()
            match = ETHERNET_RE.match(interface)
            if match:
                intf_no = interface[len(match.groups()[0]):]
                
                for token in intf_no.split('/'):
                    if int(token) < 1:
                        log.warning('Unable to expand '
                                    'interface range: %s '
                                    '(invalid interface number)' % 
                                    group)
                        raise TypeError('Unable to expand '
                                        'interface range: %s '
                                        '(invalid interface number)' % 
                                        group)

                prefix = 'Ethernet'
                items.add('%s%s' % (prefix, intf_no))
            else:
                match = MANAGEMENT_RE.match(interface)
                if match:
                    intf_no = interface[len(match.groups()[0]):]

                    for token in intf_no.split('/'):
                        if int(token) < 1:
                            log.warning('Unable to expand '
                                        'interface range: %s '
                                        '(invalid interface number)' % 
                                        group)
                            raise TypeError('Unable to expand '
                                            'interface range: %s '
                                            '(invalid interface number)' % 
                                            group)

                    prefix = 'Management'
                    items.add('%s%s' % (prefix, intf_no))
                else:
                    match = INTERFACE_NO_RE.match(interface)
                    if match:

                        for token in interface.split('/'):
                            if int(token) < 1:
                                log.warning('Unable to expand '
                                            'interface range: %s '
                                            '(invalid interface number)' % 
                                            group)
                                raise TypeError('Unable to expand '
                                                'interface range: %s '
                                                '(invalid interface number)' % 
                                                group)

                        items.add('%s%s' % (prefix, interface))
                    else:
                        
                        log.warning('Unable to expand interface range: %s '
                                    '(invalid interface)' % group)
                        raise TypeError('Unable to expand interface range: %s '
                                        '(invalid interface)' % group)
        elif len(ranges) == 2:
            [start, end] = [x.lower() for x in ranges]
            
            items_len = len(items)
            for regex, intf_type in [(ETHERNET_RE, 'Ethernet'),
                                     (MANAGEMENT_RE, 'Management'),
                                     (INTERFACE_NO_RE, prefix)]:
                match_start =  regex.match(start)
                if match_start:
                    if regex != INTERFACE_NO_RE:
                        start_intf_tokens = \
                            start[len(match_start.groups()[0]):].split('/')
                    else:
                        start_intf_tokens = start.split('/')

                    match_end = regex.match(end)
                    end_intf_tokens = None
                    if match_end:
                        if regex != INTERFACE_NO_RE:
                            end_intf_tokens = \
                                end[len(match_end.groups()[0]):].split('/')
                        else:
                            end_intf_tokens = end.split('/')
                    else:
                        match_end = INTERFACE_NO_RE.match(end)
                        if match_end:
                            end_intf_tokens = end.split('/')

                    if not end_intf_tokens:
                        log.warning('Unable to expand '
                                    'interface range: %s '
                                    '(invalid range end)' % group)

                        raise TypeError('Unable to expand '
                                        'interface range: %s '
                                        '(invalid range end)' % group)

                    if start_intf_tokens[:-1] != end_intf_tokens[:-1]:
                        log.warning('Unable to expand '
                                    'interface range: %s '
                                    '(invalid range)' % group)
                        raise TypeError('Unable to expand '
                                        'interface range: %s '
                                        '(invalid range)' % group)

                    start_index = int(start_intf_tokens[-1])
                    end_index = int(end_intf_tokens[-1])
                    if start_index >= end_index:
                        log.warning('Unable to expand '
                                    'interface range: %s '
                                    '(non-increasing range)' % 
                                    group)
                        raise TypeError('Unable to expand '
                                        'interface range: %s '
                                        '(non-increasing range)' % 
                                        group)

                    if start_index < 1 or end_index < 1:
                        log.warning('Unable to expand '
                                    'interface range: %s '
                                    '(invalid interface number)' % 
                                    group)
                        raise TypeError('Unable to expand '
                                        'interface range: %s '
                                        '(invalid interface number)' % 
                                        group)
                    
                    for index in range(start_index, 
                                       end_index):
                        prefix = intf_type
                        items.add('%s%s' % 
                                  (intf_type,
                                   '/'.join(start_intf_tokens[:-1] + 
                                            [str(index)])))
            if items_len == len(items):
                log.warning('Unable to expand interface range: %s ' % 
                            group)
                raise TypeError('Unable to expand interface range: %s ' % 
                                group)
        else:
            log.warning('Unable to expand interface range: %s '
                        '(invalid input)' % group)
            raise TypeError('Unable to expand interface range: %s '
                            '(invalid input)' % group)

    log.debug('%s expanded to: %s' % (interfaces, items))
    return items

def parse_interface(neighbor, node_id):
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
            log.error('%s: interface parse error: invalid peer device %s' % 
                      (node_id, remote_device))
            raise Exception('%s: interface parse error: invalid peer '
                            'device %s' % (node_id, remote_device))
        
        remote_interface = str(remote_interface).strip()
        if len(remote_interface.split()) != 1:
            log.error('%s: interface parse error: invalid '
                      'peer interface %s' %
                      (node_id, remote_interface))
            raise Exception('%s: interface parse error: invalid peer '
                            'interface %s' % 
                            (node_id, remote_interface))

        return (remote_device, remote_interface)
    except KeyError as err:
        log.error('%s: interface parse error: missing attribute (%s)' % 
                  (node_id, str(err)))
        raise Exception('%s: interface parse error: missing '
                        'attribute (%s)' % (node_id, str(err)))

def url_path_join(*parts):
    """Normalize url parts and join them with a slash."""
    # pylint: disable=W0142
    schemes, netlocs, paths, queries, fragments = \
        zip(*(urlsplit(part) for part in parts))
    scheme = get_first_token(schemes)
    netloc = get_first_token(netlocs)
    path = '/'.join(x.strip('/') for x in paths if x)
    query = get_first_token(queries)
    fragment = get_first_token(fragments)
    return urlunsplit((scheme, netloc, path, query, fragment))

def get_first_token(sequence):
    return next((x for x in sequence if x), '')

def all_files(path):
    result = []
    for top, _, files in os.walk(path):
        result += [os.path.join(top, f) for f in files]
    return result
