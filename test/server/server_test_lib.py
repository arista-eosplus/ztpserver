# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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

import json
import os
import random
import shutil
import string        #pylint: disable=W0402

import yaml

WORKINGDIR = '/tmp/ztpserver'

def random_string():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(random.randint(3, 20)))

def random_json(keys=None):
    data = dict()
    if keys:
        for key in keys:
            data[key] = random_string()
    else:
        for _ in range(0, 5):
            data[random_string()] = random_string()
    return json.dumps(data)

def remove_all():
    if os.path.exists(WORKINGDIR):
        shutil.rmtree(WORKINGDIR)

def add_folder(name=None):
    if not name:
        name = random_string()
    filepath = os.path.join(WORKINGDIR, name)
    if os.path.exists(filepath):
        shutil.rmtree(filepath)
    os.makedirs(filepath)
    return filepath

def write_file(contents, filename=None, mode='w'):
    if not filename:
        filename = random_string()
    if not os.path.exists(WORKINGDIR):
        os.makedirs(WORKINGDIR)
    filepath = os.path.join(WORKINGDIR, filename)
    open(filepath, mode).write(contents)
    return filepath

def ztp_headers():
    return {
        'X-Arista-Systemmac': random_string(),
        'X-Arista-Serialnum': random_string(),
        'X-Arista-Architecture': random_string(),
        'X-Arista-Modelname': random_string(),
        'X-Arista-Softwareversion': random_string()
    }

class SerializerMixin(object):
    def as_dict(self):
        raise NotImplementedError

    def as_yaml(self):
        return yaml.dump(self.as_dict())

    def as_json(self):
        return json.dumps(self.as_dict())

class Definition(SerializerMixin):

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.attributes = kwargs.get('attributes', dict())
        self.actions = kwargs.get('actions', list())

    def add_attribute(self, key, value):
        self.attributes[key] = value

    def add_action(self, **kwargs):
        action = dict()
        action['name'] = kwargs.get('name', 'test action')
        action['action'] = kwargs.get('action', 'test_action')
        action['attributes'] = kwargs.get('attributes', dict())
        self.actions.append(action)

    def as_dict(self):
        return dict(name=self.name,
                    attributes=self.attributes,
                    actions=self.actions)

def create_definition():
    return Definition()

class Attributes(SerializerMixin):

    def __init__(self, **kwargs):
        self.attributes = kwargs.get('attributes', dict())

    def add_attribute(self, key, value):
        self.attributes[key] = value

    def add_attributes(self, attributes):
        assert isinstance(attributes, dict)
        for key, value in attributes.items():
            self.add_attribute(key, value)

    def as_dict(self):
        return self.attributes

def create_attributes():
    return Attributes()

class Node(SerializerMixin):

    def __init__(self, **kwargs):
        self.serialnumber = kwargs.get('serialnumber', random_string())
        self.model = kwargs.get('model', random_string())
        self.version = kwargs.get('version', random_string())
        self.systemmac = kwargs.get('systemmac', random_string())
        self.neighbors = kwargs.get('neighbors', dict())

    def add_neighbor(self, key, value):
        self.neighbors[key] = value

    def add_neighbors(self, neighbors):
        assert isinstance(neighbors, dict)
        for key, value in neighbors.items():
            self.add_neighbor(key, value)

    def as_dict(self):
        return dict(systemmac=self.systemmac,
                    serialnumber=self.serialnumber,
                    model=self.model,
                    version=self.version,
                    neighbors=self.neighbors)

def create_node():
    return Node()

class BootstrapConf(SerializerMixin):
    def __init__(self, **kwargs):
        self.logging = kwargs.get('logging', list())
        self.xmpp = kwargs.get('xmpp', dict())

    def add_logging(self, entry):
        self.logging.append(entry)

    def as_dict(self):
        return dict(logging=self.logging, xmpp=self.xmpp)

def create_bootstrap_conf():
    return BootstrapConf()

