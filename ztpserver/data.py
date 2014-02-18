#
# Copyright (c) 2013, Arista Networks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import collections

import ztpserver.config
import ztpserver.serializers

serializer = ztpserver.serializers.Serializer()

class Data(collections.Mapping):

    def __init__(self):
        self._data = dict()

    def __getitem__(self, key):
        return self._data.get(key)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

class DataFile(Data):

    def load(self, filename, content_type='text/plain'):
        fh = open(filename, 'r').read()
        self._data = serializer.deserialize(fh, content_type)

    def dump(self, filename, content_type='text/plain'):
        data = serializer.serialize(self._data, content_type)
        open(filename, 'w').write(data)

class NodeDb(DataFile):

    def load(self):
        filename = ztpserver.config.runtime.db.nodedb
        super(NodeDb, self).load(filename, 'application/yaml')

    def dump(self):
        filename = ztpserver.config.runtime.db.nodedb
        super(NodeDb, self).dump(filename, 'application/yaml')

    def insert(self, name, definition):
        """ inserts a node into the node db """

        self._data[name] = definition

    def delete(self, name):
        """ deletes a node specified by name """

        try:
            del self._data[name]
        except KeyError:
            return

    def has_node(self, name):
        """ returns the existence of a node in node db """

        return name in self._data





