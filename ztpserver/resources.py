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

import importlib.machinery
import importlib.util
import os
import sys

from ztpserver.config import runtime


def resource_plugins():
    path = os.path.join(runtime.default.data_root, "plugins")

    plugins = []
    for _, _, filenames in os.walk(path):
        plugins.extend(filenames)
        break
    return plugins


def run_plugin(plugin, node_id, pool, node):
    filename = os.path.join(runtime.default.data_root, "plugins", plugin)
    try:
        if plugin not in sys.modules:
            loader = importlib.machinery.SourceFileLoader(plugin, filename)
            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin] = module
            spec.loader.exec_module(module)

        module = sys.modules[plugin]
        return module.main(node_id, pool, node)
    except Exception as exc:
        raise RuntimeError(f"failed to run plugin: {exc}") from exc
