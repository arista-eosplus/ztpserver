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
    remove_file,
    startup_config_action,
)


class FailureTest(ActionFailureTest):
    def test_missing_url(self):
        self.basic_test("install_extension", "Missing attribute('url')")

    def test_url_failure(self):
        self.basic_test(
            "install_extension",
            "Unable to retrieve extension from URL",
            attributes={"url": random_string()},
        )


class SuccessTest(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        extension = random_string()
        url = extension

        extension_force = random_string()
        url_force = "http://{}/{}".format(bootstrap.server, extension_force)

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"url": url}},
                {"action": "test_action_force", "attributes": {"url": url_force, "force": True}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        extensions_dir = "/tmp/extensions"
        boot_extensions = "/tmp/boot-extensions"
        action = get_action("install_extension")
        action = action.replace("/mnt/flash/.extensions", extensions_dir)
        action = action.replace("/mnt/flash/boot-extensions", boot_extensions)

        bootstrap.ztps.set_action_response("test_action", action)
        contents = random_string()
        bootstrap.ztps.set_file_response(extension, contents)

        bootstrap.ztps.set_action_response("test_action_force", action)
        contents_force = random_string()
        bootstrap.ztps.set_file_response(extension_force, contents_force)

        bootstrap.start_test()

        try:
            ext_filename = "{}/{}".format(extensions_dir, extension)
            self.assertTrue(os.path.isfile(ext_filename))
            self.assertTrue([contents] == file_log(ext_filename))
            self.assertTrue(extension in file_log(boot_extensions))

            ext_filename_force = "{}/{}".format(extensions_dir, extension_force)
            self.assertTrue(os.path.isfile(ext_filename_force))

            self.assertTrue([contents_force] == file_log(ext_filename_force))
            self.assertTrue("{} force".format(extension_force) in file_log(boot_extensions))

            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            shutil.rmtree(extensions_dir)
            remove_file(boot_extensions)
            bootstrap.end_test()

    def test_url_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        extension = random_string()
        url = "http://{}/{}".format(bootstrap.server, extension)

        extension_force = random_string()
        url_force = "http://{}/{}".format(bootstrap.server, extension_force)

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"url": url}},
                {"action": "test_action_force", "attributes": {"url": url_force, "force": True}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        extensions_dir = "/tmp/extensions"
        boot_extensions = "/tmp/boot-extensions"
        action = get_action("install_extension")
        action = action.replace("/mnt/flash/.extensions", extensions_dir)
        action = action.replace("/mnt/flash/boot-extensions", boot_extensions)

        bootstrap.ztps.set_action_response("test_action", action)
        contents = random_string()
        bootstrap.ztps.set_file_response(extension, contents)

        bootstrap.ztps.set_action_response("test_action_force", action)
        contents_force = random_string()
        bootstrap.ztps.set_file_response(extension_force, contents_force)

        bootstrap.start_test()

        try:
            ext_filename = "{}/{}".format(extensions_dir, extension)
            self.assertTrue(os.path.isfile(ext_filename))
            self.assertTrue([contents] == file_log(ext_filename))
            self.assertTrue(extension in file_log(boot_extensions))

            ext_filename_force = "{}/{}".format(extensions_dir, extension_force)
            self.assertTrue(os.path.isfile(ext_filename_force))

            self.assertTrue([contents_force] == file_log(ext_filename_force))
            self.assertTrue("{} force".format(extension_force) in file_log(boot_extensions))

            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            shutil.rmtree(extensions_dir)
            remove_file(boot_extensions)
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
