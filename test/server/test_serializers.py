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

import os
import random
import unittest

import ztpserver.serializers as serializers

from ztpserver.constants import CONTENT_TYPE_JSON

TMP_FILE = '/tmp/test_serializers-%s' % os.getpid()

def get_data():
    result = {}
    for _ in range(random.randint(10, 100)):
        key = 'x' * random.randint(0, 10)
        value = 'x' * random.randint(0, 50)
        result[key] = value

    return result

class SerializersUnitTest(unittest.TestCase):

    def test_dump_success(self):
        pass

    def test_dumps_success(self):
        pass

    def test_load_success(self):
        pass

    def test_loads_success(self):
        pass

    @classmethod
    def test_stress(cls):
        # stress test writing and loading the same file over and
        # over again and make sure the file does not get corrupted
        # in the process
        index = 0
        while index < 100:
            index += 1
            data = get_data()
            serializers.dump(data, TMP_FILE, 
                             CONTENT_TYPE_JSON)
            assert serializers.load(TMP_FILE, 
                                    CONTENT_TYPE_JSON) == data

if __name__ == '__main__':
    unittest.main()
