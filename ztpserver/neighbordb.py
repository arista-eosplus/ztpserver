# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0103,W1201
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
import ztpserver.topology

from ztpserver.constants import CONTENT_TYPE_YAML

log = logging.getLogger(__name__)

topology = ztpserver.topology.Topology()

def default_filename():
    filepath = ztpserver.config.runtime.default.data_root
    filename = ztpserver.config.runtime.neighbordb.filename
    return os.path.join(filepath, filename)

def load(filename=None):
    if filename is None:
        filename = default_filename()
    try:
        topology.load(open(filename))
        log.debug('Loaded neighbordb [%r]' % topology)
    except IOError:
        log.warn('Neighbordb file [%s] not loaded' % filename)

def create_node(nodeattrs):
    ''' extracts node attributes from nodeattrs and returns
    an instanct of :py:class:`Node`.  The only required value
    to create the object is systemmac.
    '''

    try:
        systemmac = str(nodeattrs.get('systemmac')).replace(':', '')
    except KeyError:
        log.debug("Unable to create node, missing required attribute(s)")
        return None

    model = str(nodeattrs.get('mode'))
    serialnumber = str(nodeattrs.get('serialnumber'))
    version = str(nodeattrs.get('version'))
    neighbors = nodeattrs.get('neighbors')

    node = ztpserver.topology.Node(systemmac, model, serialnumber,
                                   version, neighbors)

    log.debug("Created node object %r" % node)

    return node

def load_pattern(filename, content_type=CONTENT_TYPE_YAML):
    pattern = ztpserver.topology.Pattern()
    pattern.load(open(filename), content_type)
    return pattern

def resources(attributes, node):
    log.debug("Start processing resources with attributes: %s" % attributes)

    _attributes = dict()
    _resources = ztpserver.topology.ResourcePool()

    for key, value in attributes.items():
        if isinstance(value, dict):
            value = resources(value, node)
        elif isinstance(value, list):
            _value = list()
            for item in value:
                match = ztpserver.topology.FUNC_RE.match(item)
                if match:
                    method = getattr(_resources, match.group('function'))
                    _value.append(method(match.group('arg'), node))
                else:
                    _value.append(item)
            value = _value
        elif isinstance(value, str):
            match = ztpserver.topology.FUNC_RE.match(value)
            if match:
                method = getattr(_resources, match.group('function'))
                value = method(match.group('arg'), node)
                log.debug('Allocated value %s for attribute %s from pool %s' % \
                    (value, key, match.group('arg')))
        log.debug("Setting %s to %s" % (key, value))
        _attributes[key] = value
    return _attributes

def startup_config(resource):
    ''' manually build a definition with a single action replace_config '''

    url = '%s/nodes/%s/startup-config' % \
            (ztpserver.config.runtime.default.server_url, str(resource))

    action = dict(name='install startup-config',
                  description='install static startup configuration',
                  action='replace_config',
                  attributes={'url': url})

    definition = dict(name='install static startup-config',
                      actions=[action],
                      attributes={})
    return definition

