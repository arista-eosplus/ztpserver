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

log = logging.getLogger(__name__)


class ResourcePoolError(Exception):
    ''' base error raised by :py:class:`Resource` '''
    pass


class ResourcePool(object):

    def __init__(self):
        cfg = ztpserver.config.runtime
        self.filepath = os.path.join(cfg.default.data_root, 'resources')
        self.data = None

    def serialize(self):
        return [(key, str(value)) for (key, value) in contents.items()]

    def load(self, pool):
        self.data = None
        filepath = os.path.join(self.filepath, pool)
        self.data = load(filepath, CONTENT_TYPE_YAML)

    def dump(self, pool):
        filepath = os.path.join(self.filepath, pool)
        dump(self, filepath, CONTENT_TYPE_YAML)

    def allocate(self, pool, node):
        try:
            match = self.lookup(pool, node)
            if match:
                log.info('Found allocated resource, returning %s', match)
                return match

            self.load(pool)
            key = next(x[0] for x in self.data.items() if x[1] is None)

            log.info('Assigning %s from pool %s to node %s',
                     key, pool, node.systemmac)

            self.data[key] = node.systemmac
            self.dump(pool)
        except StopIteration:
            log.warning('No resources available in pool %s', pool)
            raise ResourcePoolError
        except Exception as exc:
            log.exception('Unable to allocate resource')
            raise ResourcePoolError
        return key

    def lookup(self, pool, node):
        ''' Return an existing allocated resource if one exists '''

        try:
            log.info('Looking up resource for node %s', node.systemmac)
            self.load(pool)
            matches = [m[0] for m in self.data.iteritems()
                       if m[1] == node.systemmac]
            key = matches[0] if matches else None
            return key
        except Exception as exc:
            log.exception('An error occurred trying to lookup existing '
                          'resource for node %s', node.systemmac)
            raise ResourcePoolError


