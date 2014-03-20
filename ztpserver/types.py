# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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
class String(object):

    def __init__(self, choices=None):
        if choices:
            choices = [str(c) for c in choices]
        self.choices = choices

    def __call__(self, value):
        value = str(value)

        if self.choices and value not in self.choices:
            raise ValueError("provided value is not a valid choice")

        return value

    def __repr__(self):
        obj = "String"
        if self.choices:
            obj += "(choices=%s)" % ','.join(self.choices)
        return obj


class Boolean(object):

    TRUEVALUES = ['yes', 'true', '1', 'on']
    FALSEVALUES = ['no', 'false', '0', 'off']

    def __call__(self, value):
        if str(value).lower() in self.TRUEVALUES:
            return True
        elif str(value).lower() in self.FALSEVALUES:
            return False
        else:
            raise ValueError

    def __repr__(self):
        return 'Boolean'

class Integer(object):

    def __init__(self, minvalue=None, maxvalue=None):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def __call__(self, value):
        try:
            value = int(value)
        except ValueError:
            raise ValueError('invalid integer provided')

        if self.minvalue is not None and value < self.minvalue:
            raise ValueError('value is less than minvalue')

        if self.maxvalue is not None and value > self.maxvalue:
            raise ValueError('value is greater than maxvalue')

        return value

    def __repr__(self):
        return "Integer(minvalue=%s, maxvalue=%s)" % \
            (self.minvalue, self.maxvalue)

class List(object):

    def __init__(self, delimiter=','):
        self.delimiter = delimiter

    def __call__(self, value):
        if isinstance(value, list):
            return value

        return str(value).split(self.delimiter)

    def __repr__(self):
        return "List(delimiter=%s)" % self.delimiter
