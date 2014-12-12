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
import os
import logging

import ztpserver.config

from ztpserver.serializers import load, dump
from ztpserver.constants import CONTENT_TYPE_YAML

log = logging.getLogger(__name__)   #pylint: disable=C0103


class ResourcePoolError(Exception):
    ''' base error raised by :py:class:`Resource` '''
    pass


class ResourcePool(object):

    def __init__(self, node_id):
        self.node_id = node_id

        cfg = ztpserver.config.runtime
        self.file_path = os.path.join(cfg.default.data_root, 'resources')
        self.data = None

    def serialize(self):
        data = dict()
        for key, value in self.data.items():
            data[key] = str(value) if value is not None else None
        return data

    def load(self, pool):
        self.data = dict()
        filename = os.path.join(self.file_path, pool)
        contents = load(filename, CONTENT_TYPE_YAML, self.node_id)
        for key, value in contents.items():
            self.data[key] = str(value) if value is not None else None
            
        log.debug('%s: loaded resource pool \'%s\': %s' % 
                  (self.node_id, pool, self.data))

    def dump(self, pool):
        log.debug('%s: writing resource pool \'%s\': %s' % (self.node_id, pool,
                                                            self.data))
        file_path = os.path.join(self.file_path, pool)
        dump(self, file_path, CONTENT_TYPE_YAML, self.node_id)

    def allocate(self, pool):
        self.load(pool)

        log.debug('%s: allocating resources from pool \'%s\': %s' % 
                  (self.node_id, pool, self.data))

        match = self.lookup(pool)

        try:
            if match:
                log.debug('%s: already allocated resource \'%s\':\'%s\'' % 
                         (self.node_id, pool, match))
                return match

            if not self.data():
                #TODO
                log.debug('self.data is really empty - this is crazy!')
                self.load(pool)

            key = next(x[0] for x in self.data.iteritems() if x[1] is None)
            log.debug('%s: allocated \'%s\':\'%s\'' % (self.node_id, pool, key))

            self.data[key] = self.node_id
            self.dump(pool)
        except StopIteration:
            log.error('%s: no resource free in \'%s\'' % (self.node_id, pool))
            raise ResourcePoolError('%s: no resource free in \'%s\'' % 
                                    (self.node_id, pool))
        except Exception as exc:
            log.error('%s: failed to allocate resource from \'%s\'' % 
                      (self.node_id, pool))
            raise ResourcePoolError(exc.message)

        return str(key)

    def lookup(self, pool):
        ''' Return an existing allocated resource if one exists '''

        log.debug('%s: looking up resource pool \'%s\': %s' % 
                  (self.node_id, pool, self.data))

        if not self.data():
                #TODO
            log.debug('self.data is empty - this is crazy!')
            self.load(pool)

        try:
            try:
                key = next(m[0] for m in self.data.iteritems()
                           if m[1] == self.node_id)
            except StopIteration:
                key = None

            return key
        except Exception as exc:
            log.error('%s: failed to lookup resource from \'%s\' (%s)' % 
                      (self.node_id, pool, exc.message))
            raise ResourcePoolError(exc.message)
