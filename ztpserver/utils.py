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
import re

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def expand_range(text):
    ''' Returns a naturally sorted list of items expanded from text. '''

    match = re.match(r'^(((E(t(h)?)?(ernet)?)?(\d+)(([\/\-\,])?(\d+))*)'
                     '(,)?)+$', 
                     text)

    if not match:
        raise TypeError('Unable to expand interface range: %s' % text)
    

    prefix = match.groups()[2]
    indicies_re = re.compile(r'[Ethernet|,]((\d(\/)?)+)(?!-)')
    range_re = re.compile(r'(\d+)\-(\d+)')

    indicies = [x[0] for x in indicies_re.findall(text)]
    ranges = range_re.findall(text)

    items = set()
    for start, end in ranges:
        start = int(start)
        end = int(end) + 1
        if end < start:
            raise TypeError('Unable to expand interface range: %s' % 
                            text)            
        for index in range(start, end):
            items.add('%s%s' % (prefix, index))

    for index in indicies:
        if index == '0' or len(index.split('/')) > 3:
            raise TypeError('Unable to expand interface range: %s' % 
                            text)            
        items.add('%s%s' % (prefix, index))

    items = list(items)
    items.sort(key=natural_keys)

    return items
