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

WORKINGDIR = '/tmp/ztpserver'

def random_string():
    return ''.join(random.choice(
            string.ascii_uppercase +
            string.digits) for _ in range(random.randint(3, 20)))

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
