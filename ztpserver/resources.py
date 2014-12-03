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
import sqlite3 as lite
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

    def dump(self, pool):
        file_path = os.path.join(self.file_path, pool)
        dump(self, file_path, CONTENT_TYPE_YAML, self.node_id)


    def allocate_from_db(self, pool, node):
        node_id = node.identifier()

        log.info('%s: looking for resources in sqlite DB. Table:%s' 
                 % (node_id, pool))

        #Setup connection to local sqlite database
        con = lite.connect('/usr/share/ztpserver/db/test.db')

        with con:
            cur = con.cursor()

            query = "SELECT * FROM `%s` WHERE node_id='%s'"  % (pool, node_id)

            log.debug('%s: executing sql query:%s' % (node_id, query))
            match = cur.execute(query).fetchall()
            
            if match:
                log.debug('%s: already allocated:%s' 
                          % (node_id, match[0]))
                return match[0]
            else:
                log.info('%s: no existing resources matches this node '
                         'in the db. Looking for new resource in %s' 
                         % (node_id, pool))
                
                # The query must use subquery since sqlite is not
                # typically compiled with LIMIT support for UPDATE
                query = """UPDATE `%s`
                           SET node_id = '%s'
                           WHERE key IN (
                             SELECT key
                             FROM `%s`
                             WHERE node_id IS NULL
                             ORDER BY rowid ASC
                             LIMIT 1
                          )""" % (pool, node_id, pool)
                log.debug('%s: executing query: %s' % (node_id, query))
                assigned = cur.execute(query).fetchone()
                log.debug('%s: number of rows affected:%s' % 
                          (node_id, cur.rowcount))

                if cur.rowcount == 1:
                    # Go get the resouce that was just allocated
                    query = "SELECT * FROM `%s` WHERE node_id='%s'" % (pool, node_id) 
                    log.debug('%s: executing sql query:%s' % (node_id, query))
                    match = cur.execute(query).fetchone()
                    return match[0]


    def allocate(self, pool, node):
        node_id = node.identifier()
        log.debug('%s: allocating resources' % node_id)

        match = self.lookup(pool, node)

        try:
            if match:
                log.debug('%s: already allocated resource \'%s\':\'%s\'' % 
                         (node_id, pool, match))
                return match

            self.load(pool)
            key = next(x[0] for x in self.data.items() if x[1] is None)

            log.debug('%s: allocated \'%s\':\'%s\'' %
                      (node_id, pool, key))

            self.data[key] = node_id
            self.dump(pool)
        except StopIteration:
            log.error('%s: no resource free in \'%s\'' % (node_id, pool))
            raise ResourcePoolError('%s: no resource free in \'%s\'' % 
                                    (node_id, pool))
        except Exception as exc:
            log.error('%s: failed to allocate resource from \'%s\'' % 
                      (node_id, pool))
            raise ResourcePoolError(exc.message)
        return str(key)

    def lookup(self, pool, node):
        ''' Return an existing allocated resource if one exists '''
        node_id = node.identifier()
        log.debug('%s: looking up resource in \'%s\'' % 
                  (node_id, pool))
        try:
            self.load(pool)
            matches = [m[0] for m in self.data.iteritems()
                       if m[1] == node_id]
            key = matches[0] if matches else None
            return key
        except Exception as exc:
            log.error('%s: failed to lookup resource from \'%s\'' % 
                      (node_id, pool))
            raise ResourcePoolError(exc.message)
