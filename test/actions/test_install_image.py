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
import unittest
from test.client.client_test_lib import (
    ActionFailureTest,
    Bootstrap,
    eapi_log,
    get_action,
    print_action,
    raise_exception,
    random_string,
    remove_file,
    startup_config_action,
)


class FailureTest(ActionFailureTest):
    def test_missing_url(self):
        self.basic_test("install_image", "Missing attribute('url')")

    def test_missing_version(self):
        self.basic_test(
            "install_image", "Missing attribute('version')", attributes={"url": random_string()}
        )

    def test_url_failure(self):
        self.basic_test(
            "install_image",
            "Unable to retrieve image file from URL",
            attributes={"url": random_string(), "version": random_string()},
        )


class SuccessTest(unittest.TestCase):
    def test_no_op(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version = random_string()
        bootstrap.eapi.version = version
        bootstrap.ztps.set_definition_response(
            actions=[
                {
                    "action": "test_action",
                    "attributes": {"url": random_string(), "version": version},
                },
                {"action": "startup_config_action"},
            ]
        )
        bootstrap.ztps.set_action_response("test_action", get_action("install_image"))
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_no_downgrade(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version1 = "4.18.1F"
        version2 = "4.17.2F"
        bootstrap.eapi.version = version1
        bootstrap.ztps.set_definition_response(
            actions=[
                {
                    "action": "test_action",
                    "attributes": {"downgrade": False, "url": random_string(), "version": version2},
                },
                {"action": "startup_config_action"},
            ]
        )
        bootstrap.ztps.set_action_response("test_action", get_action("install_image"))
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.start_test()

        image_file = "{}/EOS-{}.swi".format(bootstrap.flash, version2)
        try:
            self.assertTrue(bootstrap.success())
            self.assertTrue("install_image: nothing to do: downgrade disabled" in bootstrap.output)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(image_file)
            bootstrap.end_test()

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        version = random_string()
        image = random_string()
        url = "http://{}/{}".format(bootstrap.server, image)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "test_action", "attributes": {"url": url, "version": version}},
                {"action": "startup_config_action"},
            ]
        )

        action = get_action("install_image")
        bootstrap.ztps.set_action_response("test_action", action)
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.ztps.set_file_response(image, print_action())
        bootstrap.start_test()

        image_file = "{}/EOS-{}.swi".format(bootstrap.flash, version)
        try:
            self.assertTrue(os.path.isfile(image_file))
            self.assertTrue(bootstrap.success())
            self.assertTrue(eapi_log()[-1] == "install source flash:EOS-{}.swi".format(version))
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(image_file)
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
