#!/usr/bin/env python
#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
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

# pylint: disable=C0209

import os
import os.path
import shutil
import unittest
from test.client.client_test_lib import (
    ActionFailureTest,
    Bootstrap,
    file_log,
    get_action,
    raise_exception,
    random_string,
    startup_config_action,
)


class FailureTest(ActionFailureTest):
    def test_missing_url(self):
        self.basic_test("install_cli_plugin", "Missing attribute('url')")

    def test_url_failure(self):
        self.basic_test(
            "install_cli_plugin",
            "Unable to retrieve CliPlugin from URL",
            attributes={"url": random_string()},
        )


class SuccessTest(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        plugin = random_string()
        url = "http://{}/{}".format(bootstrap.server, plugin)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"url": url}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        plugin_dir = "/tmp"
        persistent_dir = "/tmp/persistent"
        action = get_action("install_cli_plugin")
        action = action.replace("/usr/lib/python2.7/site-packages/CliPlugin", plugin_dir)

        action = action.replace("/mnt/flash/.ztp-plugins", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(plugin, contents)
        bootstrap.start_test()

        try:
            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue("sudo cp {}/{} {}".format(persistent_dir, plugin, plugin_dir) in log)

            self.assertTrue(contents in file_log("{}/{}".format(persistent_dir, plugin)))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            shutil.rmtree(persistent_dir)
            bootstrap.end_test()

    def test_ztps_path_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        plugin = url = random_string()
        ztps_server = "http://{}".format(bootstrap.server)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"url": url, "ztps_server": ztps_server}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        plugin_dir = "/tmp"
        persistent_dir = "/tmp/persistent"
        action = get_action("install_cli_plugin")
        action = action.replace("/usr/lib/python2.7/site-packages/CliPlugin", plugin_dir)

        action = action.replace("/mnt/flash/.ztp-plugins", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(plugin, contents)
        bootstrap.start_test()

        try:
            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue("sudo cp {}/{} {}".format(persistent_dir, plugin, plugin_dir) in log)

            self.assertTrue(contents in file_log("{}/{}".format(persistent_dir, plugin)))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            shutil.rmtree(persistent_dir)
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
