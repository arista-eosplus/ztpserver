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

    def __init__(self):
        cfg = ztpserver.config.runtime
        self.filepath = os.path.join(cfg.default.data_root, 'resources')
        self.data = None

    def serialize(self):
        data = dict()
        for key, value in self.data.items():
            data[key] = str(value) if value is not None else None
        return data

    def load(self, pool):
        self.data = dict()
        filepath = os.path.join(self.filepath, pool)
        contents = load(filepath, CONTENT_TYPE_YAML)
        for key, value in contents.items():
            self.data[key] = str(value) if value is not None else None

    def dump(self, pool):
        filepath = os.path.join(self.filepath, pool)
        dump(self, filepath, CONTENT_TYPE_YAML)

    def allocate(self, pool, node):
        node_id = node.identifier()
        log.debug('Allocating resource for node %s' % node_id)
        try:
            match = self.lookup(pool, node)
            if match:
                log.debug('Resource for node %r already allocated: %s' % 
                         (node_id, match))
                return match

            self.load(pool)
            key = next(x[0] for x in self.data.items() if x[1] is None)

            log.debug('Allocating %s from pool %s to node %s' %
                      (key, pool, node_id))

            self.data[key] = node_id
            self.dump(pool)
        except StopIteration:
            log.warning('No resources available in pool %s for %s' % 
                        (pool, node_id))
            raise ResourcePoolError
        except Exception as exc:
            log.error('Failed to allocate resource for node %s: %s' % 
                      (node_id, exc))
            raise ResourcePoolError('Failed to allocate resource '
                                    'for node %s: %s' % (node_id, exc))
        return key

    def lookup(self, pool, node):
        ''' Return an existing allocated resource if one exists '''
        node_id = node.identifier()
        log.debug('Looking up resource for node %s' % node_id)
        try:
            self.load(pool)
            matches = [m[0] for m in self.data.iteritems()
                       if m[1] == node_id]
            key = matches[0] if matches else None
            return key
        except Exception as exc:
            log.error('Failed to lookup resource for node %s: %s' % 
                      (node_id, exc))
            raise ResourcePoolError('Failed to lookup resource '
                                    'for node %s: %s' % (node_id, exc))
