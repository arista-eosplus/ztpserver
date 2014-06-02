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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0103
#
import os
import logging

import ztpserver.config
import ztpserver.topology

from ztpserver.topology import Topology, TopologyError
from ztpserver.topology import Node

from ztpserver.constants import CONTENT_TYPE_YAML
from ztpserver.serializers import load, dump, SerializerError

log = logging.getLogger(__name__)

def default_filename():
    filepath = ztpserver.config.runtime.default.data_root
    filename = ztpserver.config.runtime.neighbordb.filename
    return os.path.join(filepath, filename)

def load(filename, content_type):
    try:
        return ztpserver.serializers.load(filename, content_type)
    except SerializerError:
        log.exception('Unable to load file %s', filename)

def load_topology(filename=None, contents=None):
    try:
        if filename is not None:
            filename = filename or default_filename()
            contents = load(filename, CONTENT_TYPE_YAML)
        elif contents is None:
            log.warning('Creating empty topology object')

        topology = Topology()
        if 'variables' in contents:
            topology.add_variables(contents['variables'])
        topology.add_patterns(contents['patterns'])

        log.info('Loaded neighbordb: %r', topology)
        return topology
    except TopologyError:
        log.warning('Unable to load neighbordb from %s', filename)
    except SerializerError:
        log.error('Unable to load topology file %s', filename)

def load_pattern(filename, content_type=CONTENT_TYPE_YAML):
    # See #44
    pattern = ztpserver.topology.Pattern(None, None, None)
    pattern.load_from_file(filename, content_type)
    return pattern

def load_node(filename, content_type=CONTENT_TYPE_YAML):
    node = ztpserver.serializers.load(filename, content_type, Node)
    return node

def create_node(nodeattrs):
    try:
        systemmac = str(nodeattrs['systemmac']).replace(':', '')
        systemmac = str(systemmac).replace('.', '')
        del nodeattrs['systemmac']
        node = Node(systemmac, **nodeattrs)
        log.debug('Created node object %r', node)
        return node
    except KeyError:
        log.warning("Unable to create node, missing required attribute(s)")

def resources(attributes, node):
    log.debug('Start processing resources with attributes: %s', attributes)

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
                log.debug('Allocated value %s for attribute %s from pool %s',
                          value, key, match.group('arg'))
        log.debug('Setting %s to %s', key, value)
        _attributes[key] = value
    return _attributes

def replace_config_action(resource, filename=None):
    ''' manually build a definition with a single action replace_config '''

    filename = filename or 'startup-config'
    server_url = ztpserver.config.runtime.default.server_url
    url = '%s/nodes/%s/%s' % (server_url, str(resource), filename)

    action = dict(name='install static startup-config file',
                  action='replace_config',
                  always_execute=True,
                  attributes={'url': url})

    return action

def create_node_definition(definition, node):
    ''' Creates the node specific definition file based on the
    definition template found at url.  The node definition file
    is created in /nodes/{systemmac}/definition.
    '''

    url = definition.get('definition')
    definition.setdefault('name', 'Autogenerated using %s' % url)
    definition.setdefault('attributes', dict())
    definition['attributes']['ztps_server'] = \
        ztpserver.config.runtime.default.server_url

    # pass the attributes through the resources function in
    # order to convert the global attributes from functions
    # to node specific values
    attributes = definition.get('attributes') or dict()
    definition['attributes'] = resources(attributes, node)

    # iterate through the list of actions to convert any
    # action specific attribute functions to node specific
    # values
    _actions = list()
    for action in definition.get('actions'):
        log.debug('Processing attributes for action %s', action['name'])
        if 'attributes' in action:
            action['attributes'] = \
                resources(action['attributes'], node)
        _actions.append(action)
    definition['actions'] = _actions

    # return the node specific definition
    return definition

