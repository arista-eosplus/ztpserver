# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0103,W1201
#
# Copyright (c) 2015, Arista Networks, Inc.
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
import unittest

import ztpserver.types

class TestTypes(unittest.TestCase):

    def test_create_string_defaults(self):
        obj = ztpserver.types.String()
        self.assertIsInstance(obj, ztpserver.types.String)

    def test_create_string_choices(self):
        obj = ztpserver.types.String(['one', 'two'])
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(repr(obj), "String(choices=one,two)")

    def test_create_string_choices_integers(self):
        obj = ztpserver.types.String([1, 2])
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(repr(obj), "String(choices=1,2)")

    def test_call_string_using_defaults_and_string(self):
        obj = ztpserver.types.String()
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(obj('hello'), 'hello')

    def test_call_string_using_defaults_and_int(self):
        obj = ztpserver.types.String()
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(obj(1), '1')

    def test_call_string_using_defaults_and_bool(self):
        obj = ztpserver.types.String()
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(obj(True), 'True')

    def test_call_string_using_defaults_and_list(self):
        obj = ztpserver.types.String()
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(obj(['one']), "['one']")

    def test_call_string_with_choices_valid(self):
        obj = ztpserver.types.String(['one', 'two'])
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(repr(obj), "String(choices=one,two)")
        self.assertEqual(obj('one'), 'one')

    def test_call_string_with_choices_invalid(self):
        obj = ztpserver.types.String(['one', 'two'])
        self.assertIsInstance(obj, ztpserver.types.String)
        self.assertEqual(repr(obj), "String(choices=one,two)")
        self.assertRaises(ValueError, obj, 'three')

    def test_create_boolean_defaults(self):
        obj = ztpserver.types.Boolean()
        self.assertIsInstance(obj, ztpserver.types.Boolean)
        self.assertEqual(repr(obj), 'Boolean')

    def test_call_boolean_true_values_valid(self):
        obj = ztpserver.types.Boolean()
        self.assertIsInstance(obj, ztpserver.types.Boolean)
        values = obj.TRUEVALUES + ['YES', 'TRUE', True, 1, 'ON']
        for value in values:
            obj(value)

    def test_call_boolean_false_values_valid(self):
        obj = ztpserver.types.Boolean()
        self.assertIsInstance(obj, ztpserver.types.Boolean)
        values = obj.FALSEVALUES + ['NO', 'FALSE', False, 0, 'OFF']
        for value in values:
            obj(value)

    def test_call_boolean_invalid_values(self):
        obj = ztpserver.types.Boolean()
        self.assertIsInstance(obj, ztpserver.types.Boolean)
        values = ['test', 100, ['one', 'two']]
        for value in values:
            self.assertRaises(ValueError, obj, value)

    def test_create_integer_defaults(self):
        obj = ztpserver.types.Integer()
        self.assertIsInstance(obj, ztpserver.types.Integer)
        self.assertEqual(repr(obj), "Integer(min_value=None, max_value=None)")

    def test_create_integer_min_value(self):
        obj = ztpserver.types.Integer(min_value=1)
        self.assertEqual(obj.min_value, 1)
        self.assertIsNone(obj.max_value)

    def test_create_integer_max_value(self):
        obj = ztpserver.types.Integer(max_value=1)
        self.assertEqual(obj.max_value, 1)
        self.assertIsNone(obj.min_value)

    def test_create_integer_range(self):
        obj = ztpserver.types.Integer(min_value=1, max_value=1)
        self.assertEqual(obj.min_value, 1)
        self.assertEqual(obj.max_value, 1)

    def test_call_integer_defaults_valid(self): #pylint: disable=R0201
        obj = ztpserver.types.Integer()
        for value in [0, 1.0, 1.1, '65535', True]:
            obj(value)

    def test_call_integer_defaults_invalid(self):
        obj = ztpserver.types.Integer()
        self.assertRaises(ValueError, obj, 'string')
        self.assertRaises(TypeError, obj, [1, 2])

    def test_call_integer_min_value_valid(self):
        obj = ztpserver.types.Integer(min_value=1)
        self.assertEqual(obj(1), 1)
        self.assertEqual(obj('1'), 1)

    def test_call_integer_min_value_invalid(self):
        obj = ztpserver.types.Integer(min_value=1)
        self.assertRaises(ValueError, obj, 0)
        self.assertRaises(ValueError, obj, '0')

    def test_call_integer_max_value_valid(self):
        obj = ztpserver.types.Integer(max_value=1)
        self.assertEqual(obj(1), 1)
        self.assertEqual(obj('1'), 1)

    def test_call_integer_max_value_invalid(self):
        obj = ztpserver.types.Integer(max_value=1)
        self.assertRaises(ValueError, obj, 2)
        self.assertRaises(ValueError, obj, '2')

    def test_call_integer_range_valid(self):
        obj = ztpserver.types.Integer(min_value=1, max_value=2)
        self.assertEqual(obj(1), 1)

    def test_call_integer_range_invalid(self):
        obj = ztpserver.types.Integer(min_value=1, max_value=2)
        self.assertRaises(ValueError, obj, 3)

    def test_create_list_defaults(self):
        obj = ztpserver.types.List()
        self.assertIsInstance(obj, ztpserver.types.List)
        self.assertEqual(repr(obj), 'List(delimiter=,)')





if __name__ == '__main__':
    unittest.main()
