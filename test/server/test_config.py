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

import collections
import os
import tempfile
import unittest

import ztpserver.config

class TestAttributes(unittest.TestCase):

    def test_attr_valid(self):
        obj = ztpserver.config.Attr('test')
        self.assertIsInstance(obj, ztpserver.config.Attr)

    def test_attr_invalid(self):
        self.assertRaises(TypeError, ztpserver.config.Attr)

    def test_strattr_defaults(self):
        obj = ztpserver.config.StrAttr('test')
        self.assertIsInstance(obj, ztpserver.config.StrAttr)

    def test_strattr_with_choices(self):
        obj = ztpserver.config.StrAttr('test', choices=['one', 'two'])
        self.assertIsInstance(obj, ztpserver.config.StrAttr)
        self.assertEqual(repr(obj.type), 'String(choices=one,two)')

    def test_strattr_with_default(self):
        obj = ztpserver.config.StrAttr('test', default='test')
        self.assertIsInstance(obj, ztpserver.config.StrAttr)
        self.assertEqual(obj.default, 'test')

    def test_strattr_with_group(self):
        obj = ztpserver.config.StrAttr('test', group='test')
        self.assertIsInstance(obj, ztpserver.config.StrAttr)
        self.assertEqual(obj.group, 'test')

    def test_strattr_with_choices_default_valid(self):
        obj = ztpserver.config.StrAttr('test', choices=['one', 'two'],
            default='one')
        self.assertIsInstance(obj, ztpserver.config.StrAttr)
        self.assertEqual(repr(obj.type), 'String(choices=one,two)')
        self.assertEqual(obj.default, 'one')

    def test_strattr_with_choices_default_invalid(self):
        self.assertRaises(ValueError, ztpserver.config.StrAttr,
            'test', choices=['one', 'two'], default='three')

    def test_strattr_with_choices_default_group(self):
        obj = ztpserver.config.StrAttr('test', choices=['one', 'two'],
            group='test', default='one')
        self.assertIsInstance(obj, ztpserver.config.StrAttr)
        self.assertEqual(repr(obj.type), 'String(choices=one,two)')
        self.assertEqual(obj.default, 'one')
        self.assertEqual(obj.group, 'test')

    def test_intattr_defaults(self):
        obj = ztpserver.config.IntAttr('test')
        self.assertIsInstance(obj, ztpserver.config.IntAttr)

    def test_intattr_with_min_value(self):
        obj = ztpserver.config.IntAttr('test', min_value=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(repr(obj.type), "Integer(min_value=1, max_value=None)")

    def test_intattr_with_max_value(self):
        obj = ztpserver.config.IntAttr('test', max_value=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(repr(obj.type), "Integer(min_value=None, max_value=1)")

    def test_intattr_with_min_and_max_value(self):
        obj = ztpserver.config.IntAttr('test', min_value=1, max_value=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(repr(obj.type), "Integer(min_value=1, max_value=1)")

    def test_intattr_with_default(self):
        obj = ztpserver.config.IntAttr('test', default=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(obj.default, 1)

    def test_intattr_with_min_valid_default(self):
        obj = ztpserver.config.IntAttr('test', min_value=1, default=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(obj.default, 1)

    def test_intattr_with_max_valid_default(self):
        obj = ztpserver.config.IntAttr('test', max_value=1, default=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(obj.default, 1)

    def test_intattr_with_range_valid_default(self):
        obj = ztpserver.config.IntAttr('test', min_value=1, max_value=1,
            default=1)
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(obj.default, 1)

    def test_intattr_with_min_invalid_default(self):
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=0, default=-1)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=1, default=0)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=2, default=1)

    def test_intattr_with_max_invalid_default(self):
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', max_value=0, default=1)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', max_value=1, default=2)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', max_value=2, default=3)

    def test_intattr_with_range_invalid_default(self):
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=0, max_value=0, default=1)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=1, max_value=0, default=2)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=1, max_value=0, default=2)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=1, max_value=1, default=2)

        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=2, max_value=0, default=3)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=0, max_value=2, default=3)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=2, max_value=2, default=3)
        self.assertRaises(ValueError, ztpserver.config.IntAttr,
            'test', min_value=2, max_value=3, default=4)

    def test_intattr_with_group(self):
        obj = ztpserver.config.IntAttr('test', group='test')
        self.assertIsInstance(obj, ztpserver.config.IntAttr)
        self.assertEqual(obj.group, 'test')

    def test_boolattr_defaults(self):
        obj = ztpserver.config.BoolAttr('test')
        self.assertIsInstance(obj, ztpserver.config.BoolAttr)
        self.assertEqual(repr(obj.type), "Boolean")

    def test_boolattr_with_default(self):
        obj = ztpserver.config.BoolAttr('test', default=True)
        self.assertIsInstance(obj, ztpserver.config.BoolAttr)
        self.assertTrue(obj.default)

    def test_boolattr_with_group(self):
        obj = ztpserver.config.BoolAttr('test', group='test')
        self.assertIsInstance(obj, ztpserver.config.BoolAttr)
        self.assertEqual(obj.group, 'test')

class TestGroup(unittest.TestCase):
    #pylint: disable=C0103

    class Config(object):
        def __init__(self):
            self.attributes = list()

        @classmethod
        def __get_attribute__(cls, name, group_name):
            return (name, group_name)

        def add_attribute(self, item, group_name):
            self.attributes.append((item, group_name))

        def __repr__(self):
            return 'Config'

    def setUp(self):
        self.config = self.Config()

    def tearDown(self):
        del self.config

    def test_group(self):
        obj = ztpserver.config.Group('test', self.config)
        self.assertIsInstance(obj, ztpserver.config.Group)
        self.assertEqual('test', obj.name)
        self.assertEqual('Config', repr(obj.config))

    def test_group_get_attr(self):
        obj = ztpserver.config.Group('test', self.config)
        self.assertEqual(obj.testattr, ('testattr', 'test'))
        self.assertEqual(obj['testattr'], ('testattr', 'test'))

    def test_group_add_attribute(self):
        obj = ztpserver.config.Group('test', self.config)
        obj.add_attribute('test')
        self.assertEqual(self.config.attributes[0], ('test', 'test'))


class TestConfig(unittest.TestCase):
    #pylint: disable=C0103

    Attr = collections.namedtuple('Attr', ['name', 'type', 'group', 'default'])
    CONF = """\n[default]\ntest = value\n[group]\ntest = value\n"""

    def setUp(self):
        self.config = ztpserver.config.Config()

    def tearDown(self):
        del self.config

    def test_config(self):
        self.assertIsInstance(self.config, ztpserver.config.Config)
        self.assertEqual(repr(self.config), 'Config')

    def test_config_add_attribute_valid(self):
        attr = self.Attr('test', str, None, None)
        self.config.add_attribute(attr)
        self.assertIsNone(getattr(self.config, 'test'))
        self.assertIn((None, 'test'), self.config.attributes)

    def test_config_add_attribute_default_value(self):
        attr = self.Attr('test', str, None, 'value')
        self.config.add_attribute(attr)
        self.assertEqual(self.config.test, 'value')

    def test_config_add_attribute_group_and_default_value(self):
        attr = self.Attr('test', str, 'group', 'value')
        self.config.add_attribute(attr)
        self.assertEqual(self.config.group.test, 'value')
        self.assertIsInstance(self.config.group, ztpserver.config.Group)

    def test_config_add_attribute_invalid(self):
        self.assertRaises(AttributeError, self.config.add_attribute, 'test')

    def test_config_add_attribute_duplicate(self):
        attr = self.Attr('test', str, None, None)
        self.config.add_attribute(attr)
        self.assertRaises(AttributeError, self.config.add_attribute, attr)

    def test_config_add_group(self):
        for grp in ['test', 100]:
            self.config.add_group(grp)
            grp = str(grp) if isinstance(grp, int) else grp
            self.assertIn(grp, self.config.groups)
            self.assertIsInstance(getattr(self.config, grp),
                                  ztpserver.config.Group)

    def test_config_set_value_attribute(self):
        attr = self.Attr('test', str, None, None)
        self.config.add_attribute(attr)
        self.config.set_value('test', 'value')
        self.assertEqual(self.config.test, 'value')

    def test_config_runtime(self):
        obj = ztpserver.config.runtime
        self.assertIsInstance(obj, ztpserver.config.Config)

    def test_config_runtime_clear_value(self):
        obj = ztpserver.config.runtime
        obj.set_value('interface', '1.1.1.1', 'server')
        self.assertEqual(obj.server.interface, '1.1.1.1')
        obj.clear_value('interface', 'server')
        self.assertEqual(obj.server.interface, '0.0.0.0')

    def test_config_runtime_set_value(self):
        obj = ztpserver.config.runtime
        obj.set_value('interface', '1.1.1.1', 'server')
        self.assertEqual(obj.server.interface, '1.1.1.1')

    def test_config_runtime_environ_env_set(self):
        os.environ['ZTPS_ENV'] = 'environ'
        obj = ztpserver.config.Config()
        attr = ztpserver.config.StrAttr(name='env',
                                        default='default',
                                        environ='ZTPS_ENV')
        obj.add_attribute(attr)
        self.assertEqual(obj.default.env, 'environ')

    def test_config_runtime_environ_env_notset(self):
        obj = ztpserver.config.Config()
        attr = ztpserver.config.StrAttr(name='env',
                                        default='default',
                                        environ='ZTPS_ENV')
        obj.add_attribute(attr)
        self.assertEqual(obj.default.env, 'default')

    def test_config_runtime_environ_env_set_no_default(self):
        os.environ['ZTPS_ENV'] = 'environ'
        obj = ztpserver.config.Config()
        attr = ztpserver.config.StrAttr(name='env',
                                        environ='ZTPS_ENV')
        obj.add_attribute(attr)
        self.assertEqual(obj.default.env, 'environ')

    def test_config_runtime_environ_env_notset_no_default(self):
        obj = ztpserver.config.Config()
        attr = ztpserver.config.StrAttr(name='env',
                                        environ='ZTPS_ENV')
        obj.add_attribute(attr)
        self.assertIsNone(obj.default.env)

    def test_load_config_file(self):
        filename = tempfile.NamedTemporaryFile(mode='w')
        filename.writelines(self.CONF)
        filename.flush()

        obj = ztpserver.config.runtime
        obj.add_attribute(ztpserver.config.StrAttr(name='test'))
        obj.add_attribute(ztpserver.config.StrAttr(name='test', group='group'))
        obj.read(filename.name)

        self.assertEqual(obj.default.test, 'value')
        self.assertEqual(obj.group.test, 'value')
        filename.close()


if __name__ == '__main__':
    unittest.main()
