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

import io
import os
import os.path
import random
import shutil
import unittest
from stat import ST_MODE
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

import six


def random_permissions():
    return "7{}{}".format(
        random.choice([1, 2, 3, 4, 5, 6, 7]), random.choice([1, 2, 3, 4, 5, 6, 7])
    )


class FailureTest(ActionFailureTest):
    def test_missing_src_url(self):
        self.basic_test("copy_file", "Missing attribute('src_url')")

    def test_missing_dst_url(self):
        self.basic_test(
            "copy_file", "Missing attribute('dst_url')", attributes={"src_url": random_string()}
        )

    def test_wrong_overwrite_value(self):
        self.basic_test(
            "copy_file",
            "Erroneous 'overwrite' value",
            attributes={
                "src_url": random_string(),
                "dst_url": random_string(),
                "overwrite": "bogus",
            },
        )

    def test_url_failure(self):
        action = get_action("copy_file")
        action = action.replace("/mnt/flash/.ztp-files", "/tmp")

        self.basic_test(
            "copy_file",
            "Unable to retrieve file from URL",
            attributes={"src_url": random_string(), "dst_url": random_string()},
            action_value=action,
        )


class SuccessSrcUrlReplacementTests(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())
        ztps_server = "http://{}".format(bootstrap.server)
        url = "http://{}/{}".format(bootstrap.server, source)

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {
                        "src_url": url,
                        "dst_url": destination,
                        "ztps_server": ztps_server,
                    },
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(destination, source)

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))
            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_append_server(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())
        ztps_server = "http://{}".format(bootstrap.server)

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {
                        "src_url": source,
                        "dst_url": destination,
                        "ztps_server": ztps_server,
                    },
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(destination, source)

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))
            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()


class SuccessPersistentTest(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"src_url": url, "dst_url": destination}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(destination, source)

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))
            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_replace(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())

        url = "http://{}/{}".format(bootstrap.server, source)
        attributes = {"src_url": url, "dst_url": destination}

        # 'replace' is the default
        if bool(random.getrandbits(1)):
            attributes["overwrite"] = "replace"

        mode = random_permissions()
        attributes["mode"] = mode

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": attributes},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = "{}/{}".format(destination, source)
        bootstrap.start_test()

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))
            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            if mode:
                self.assertTrue(mode == oct(os.stat(destination_path)[ST_MODE])[-3:])
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_keep_original(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {
                        "src_url": url,
                        "dst_url": destination,
                        "overwrite": "if-missing",
                    },
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = "{}/{}".format(destination, source)
        existing_contents = random_string()
        os.makedirs(destination)
        with io.open(destination_path, "w", encoding="utf8") as file_descriptor:
            file_descriptor.write(six.ensure_text(existing_contents))

        bootstrap.start_test()

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([existing_contents] == file_log(destination_path))

            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            shutil.rmtree(destination)
            bootstrap.end_test()

    def test_keep_backup(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = "/tmp/{}".format(random_string())

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {"src_url": url, "dst_url": destination, "overwrite": "backup"},
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("copy_file")

        # Make the destinaton persistent
        action = action.replace(
            "PERSISTENT_STORAGE = [", "PERSISTENT_STORAGE = ['{}', ".format(destination)
        )
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = "{}/{}".format(destination, source)
        backup_contents = random_string()
        os.makedirs(destination)
        with io.open(destination_path, "w", encoding="utf8") as file_descriptor:
            file_descriptor.write(six.ensure_text(backup_contents))

        bootstrap.start_test()

        backup_path = "{}.backup".format(destination_path)
        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))

            self.assertTrue(os.path.isfile(backup_path))
            self.assertTrue([backup_contents] == file_log(backup_path))

            self.assertFalse(os.path.isfile(bootstrap.rc_eos))
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            remove_file(backup_path)
            shutil.rmtree(destination)
            bootstrap.end_test()


class SuccessNonPersistentTest(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": {"src_url": url, "dst_url": destination}},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        persistent_dir = "/tmp"
        action = get_action("copy_file")
        action = action.replace("/mnt/flash/.ztp-files", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(persistent_dir, source)

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))

            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue("sudo cp {} {}".format(destination_path, destination) in log)
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_replace(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = "http://{}/{}".format(bootstrap.server, source)
        attributes = {"src_url": url, "dst_url": destination}

        # 'replace' is the default
        if bool(random.getrandbits(1)):
            attributes["overwrite"] = "replace"

        mode = random_permissions()
        attributes["mode"] = mode

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "test_action", "attributes": attributes},
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        persistent_dir = "/tmp"
        action = get_action("copy_file")
        action = action.replace("/mnt/flash/.ztp-files", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        destination_path = "{}/{}".format(persistent_dir, source)
        bootstrap.start_test()

        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))

            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue("sudo cp {} {}".format(destination_path, destination) in log)
            if mode:
                self.assertTrue("sudo chmod {} {}".format(mode, destination) in log)
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_original(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {
                        "src_url": url,
                        "dst_url": destination,
                        "overwrite": "if-missing",
                    },
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        persistent_dir = "/tmp"
        action = get_action("copy_file")
        action = action.replace("/mnt/flash/.ztp-files", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(persistent_dir, source)
        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))

            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue(
                "[ ! -f {destination} ] && sudo cp {} {destination}".format(
                    destination_path, destination=destination
                )
                in log
            )
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()

    def test_keep_backup(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        source = random_string()
        destination = random_string()

        url = "http://{}/{}".format(bootstrap.server, source)
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {"src_url": url, "dst_url": destination, "overwrite": "backup"},
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        persistent_dir = "/tmp"
        action = get_action("copy_file")
        action = action.replace("/mnt/flash/.ztp-files", persistent_dir)
        bootstrap.ztps.set_action_response("test_action", action)

        contents = random_string()
        bootstrap.ztps.set_file_response(source, contents)

        bootstrap.start_test()

        destination_path = "{}/{}".format(persistent_dir, source)
        try:
            self.assertTrue(os.path.isfile(destination_path))
            self.assertTrue([contents] == file_log(destination_path))

            self.assertTrue(os.path.isfile(bootstrap.rc_eos))
            log = file_log(bootstrap.rc_eos)
            self.assertTrue("#!/bin/bash" in log)
            self.assertTrue("sudo cp {} {}".format(destination_path, destination) in log)
            self.assertTrue(
                "[ -f {destination} ] && sudo mv {destination} {destination}.backup".format(
                    destination=destination
                )
                in log
            )
            self.assertTrue(bootstrap.success())
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            remove_file(destination_path)
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
