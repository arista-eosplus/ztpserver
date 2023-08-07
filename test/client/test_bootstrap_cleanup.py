#!/usr/bin/env python
#
# Copyright (c) 2015 Arista Networks, Inc.
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

import io
import os
import os.path
import unittest
from test.client.client_test_lib import (
    Bootstrap,
    fail_flash_file_action,
    raise_exception,
    random_string,
    startup_config_action,
)

from six import ensure_text

# pylint: disable=R0904,F0401


class BootstrapCleanupTest(unittest.TestCase):
    def test_action_failure(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()

        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])

        flash_filename = random_string()
        bootstrap.ztps.set_action_response(
            "test_action", fail_flash_file_action(bootstrap.flash, flash_filename)
        )

        with io.open(bootstrap.rc_eos, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        with io.open(bootstrap.startup_config, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        with io.open(bootstrap.boot_extensions, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        os.mkdir(bootstrap.boot_extensions_folder)
        with io.open(
            os.path.join(bootstrap.boot_extensions_folder, "my_extension"), "w", encoding="utf8"
        ) as fd:
            fd.write(ensure_text(random_string()))

        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.action_failure())
            self.assertFalse(bootstrap.error)
            self.assertFalse(os.path.isfile(os.path.join(bootstrap.flash, flash_filename)))
            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertFalse(os.path.isfile(bootstrap.startup_config))
            self.assertFalse(os.path.isfile(bootstrap.boot_extensions))
            self.assertFalse(os.path.isdir(bootstrap.boot_extensions_folder))
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_success(self):
        bootstrap = Bootstrap()

        startup_config = random_string()

        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])
        bootstrap.ztps.set_action_response("test_action", startup_config_action([startup_config]))

        with io.open(bootstrap.rc_eos, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        with io.open(bootstrap.startup_config, "w", encoding="utf8") as fd:
            fd.write(ensure_text(startup_config + random_string()))
        with io.open(bootstrap.boot_extensions, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        os.mkdir(bootstrap.boot_extensions_folder)
        with io.open(
            os.path.join(bootstrap.boot_extensions_folder, "my_extension"), "w", encoding="utf8"
        ) as fd:
            fd.write(ensure_text(random_string()))

        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertFalse(bootstrap.error)

            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            with io.open(bootstrap.startup_config, encoding="utf8") as fd:
                self.assertTrue(fd.read() == startup_config)
            self.assertFalse(os.path.isfile(bootstrap.boot_extensions))
            self.assertFalse(os.path.isdir(bootstrap.boot_extensions_folder))
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
