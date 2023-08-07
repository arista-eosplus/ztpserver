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
import unittest
from test.client.client_test_lib import (
    Bootstrap,
    erroneous_action,
    exception_action,
    fail_action,
    file_log,
    missing_main_action,
    print_action,
    raise_exception,
    random_string,
    remove_file,
    startup_config_action,
    wrong_signature_action,
)

from six import ensure_text

# pylint: disable=R0904,F0401


class ServerNotRunningTest(unittest.TestCase):
    def test(self):
        bootstrap = Bootstrap(server="unkown")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.server_connection_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class ConfigRequestErrorTest(unittest.TestCase):
    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(status=201)
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(status=201, content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class EAPIErrorTest(unittest.TestCase):
    def test(self):
        bootstrap = Bootstrap(eapi_port=54321)
        bootstrap.ztps.set_config_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_configured())
            self.assertTrue(bootstrap.eapi_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class CheckNodeErrorTest(unittest.TestCase):
    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(status=200)
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(status=200, content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_node_not_found(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(status=400)
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.node_not_found_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_bogus_location(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response(location="bogus_location")
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.server_connection_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class DefinitionErrorTest(unittest.TestCase):
    def test_definition_missing(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.server_connection_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(status=201)

        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(status=201, content_type="text/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_bogus_definition_response(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_bogus_definition_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.invalid_definition_format())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_topology_check(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(status=400, content_type="text/html")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.toplogy_check_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class MissingStartupConfigTest(unittest.TestCase):
    def test(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.missing_startup_config_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class FactoryDefaultTest(unittest.TestCase):
    def test(self):
        bootstrap = Bootstrap()

        with io.open(bootstrap.rc_eos, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        with io.open(bootstrap.boot_extensions, "w", encoding="utf8") as fd:
            fd.write(ensure_text(random_string()))
        os.makedirs(bootstrap.boot_extensions_folder)
        with io.open(
            os.path.join(bootstrap.boot_extensions_folder, random_string()), "w", encoding="utf8"
        ) as fd:
            fd.write(ensure_text(random_string()))

        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.missing_startup_config_failure())
            self.assertFalse(os.path.exists(bootstrap.rc_eos))
            self.assertFalse(os.path.exists(bootstrap.boot_extensions))
            self.assertFalse(os.path.exists(bootstrap.boot_extensions_folder))

            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class FileLogConfigTest(unittest.TestCase):
    def test(self):
        filenames = {
            "DEBUG": "/tmp/ztps-log-{}-debug".format(os.getpid()),
            "ERROR": "/tmp/ztps-log-{}-error".format(os.getpid()),
            "INFO": "/tmp/ztps-log-{}-info".format(os.getpid()),
            "bogus": "/tmp/ztps-log-{}-bogus".format(os.getpid()),
        }

        logging = []
        for level, filename in filenames.items():
            logging += ({"destination": "file:{}".format(filename), "level": level},)

        for filename in filenames.values():
            self.assertFalse(os.path.isfile(filename))

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=logging)
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.missing_startup_config_failure())
            for filename in filenames.values():
                self.assertTrue(file_log(filename))
            self.assertEqual(
                file_log(filenames["DEBUG"], ignore_string="SyslogManager"),
                file_log(filenames["bogus"], ignore_string="SyslogManager"),
            )
            self.assertEqual(
                file_log(filenames["DEBUG"], ignore_string="SyslogManager"),
                file_log(filenames["INFO"], ignore_string="SyslogManager"),
            )
            self.assertNotEqual(
                file_log(filenames["DEBUG"], ignore_string="SyslogManager"),
                file_log(filenames["ERROR"], ignore_string="SyslogManager"),
            )
            self.assertTrue(
                set(file_log(filenames["ERROR"])).issubset(set(file_log(filenames["DEBUG"])))
            )
            for filename in filenames.values():
                remove_file(filename)
                self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class ActionFailureTest(unittest.TestCase):
    def action_fail_test(self, action):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])
        bootstrap.ztps.set_action_response("test_action", action)
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.action_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_return_code_action_failed(self):
        self.action_fail_test(fail_action())

    def test_erroneous_action_failed(self):
        self.action_fail_test(erroneous_action())

    def test_missing_main_action_failed(self):
        self.action_fail_test(missing_main_action())

    def test_wrong_sig_action_failed(self):
        self.action_fail_test(wrong_signature_action())

    def test_exception_action_failed(self):
        self.action_fail_test(exception_action())

    def test_status(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])
        bootstrap.ztps.set_action_response("test_action", print_action(), status=201)
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])
        bootstrap.ztps.set_action_response("test_action", print_action(), content_type="test/plain")
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_status_content_type(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "test_action"}])
        bootstrap.ztps.set_action_response(
            "test_action", print_action(), status=201, content_type="test/plain"
        )
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.unexpected_response_failure())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_action_failure_log(self):
        log = "/tmp/ztps-log-{}-debug".format(os.getpid())

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(
            logging=[
                {"destination": "file:{}".format(log), "level": "DEBUG"},
            ]
        )
        bootstrap.ztps.set_node_check_response()

        text_onstart = random_string()
        text_onsuccess = random_string()
        text_onfailure = random_string()
        bootstrap.ztps.set_definition_response(
            actions=[
                {
                    "action": "test_action",
                    "onstart": text_onstart,
                    "onsuccess": text_onsuccess,
                    "onfailure": text_onfailure,
                },
            ]
        )
        bootstrap.ztps.set_action_response("test_action", fail_action())
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected(), "0")
            self.assertTrue(bootstrap.action_failure(), "1")
            self.assertFalse(bootstrap.error)
            log = "".join(file_log(log))
            self.assertTrue("test_action: {}".format(text_onstart) in log, "2")
            self.assertTrue("test_action: {}".format(text_onsuccess) not in log, "3")
            self.assertTrue("test_action: {}".format(text_onfailure) in log, "4")
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


class BootstrapSuccessTest(unittest.TestCase):
    def test_success(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(actions=[{"action": "startup_config_action"}])
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_multiple_actions(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "print_action_1"},
                {"action": "print_action_2"},
            ]
        )
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        text_1 = random_string()
        bootstrap.ztps.set_action_response("print_action_1", print_action(text_1))
        text_2 = random_string()
        bootstrap.ztps.set_action_response("print_action_2", print_action(text_2))
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertTrue(text_1 in bootstrap.output)
            self.assertTrue(text_2 in bootstrap.output)
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_duplicate_actions(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "print_action"},
                {"action": "print_action"},
            ]
        )
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        text = random_string()
        bootstrap.ztps.set_action_response("print_action", print_action(text))
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertTrue(bootstrap.output.count("Downloading action print_action") == 1)
            self.assertTrue(bootstrap.output.count("Executing action print_action") == 2)
            self.assertTrue(bootstrap.output.count(text) == 2)
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_attribute_copy(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        text = random_string()
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "print_action", "attributes": {"print_action-attr": text}},
            ]
        )
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.ztps.set_action_response(
            "print_action", print_action(use_attribute=True, create_copy=True)
        )
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertTrue(text in bootstrap.output)
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_attribute(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_node_check_response()
        text = random_string()
        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {"action": "print_action", "attributes": {"print_action-attr": text}},
            ]
        )
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.ztps.set_action_response("print_action", print_action(use_attribute=True))
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertTrue(text in bootstrap.output)
            self.assertFalse(bootstrap.error)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()

    def test_action_success_log(self):
        log = "/tmp/ztps-log-{}-debug".format(os.getpid())

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(
            logging=[
                {"destination": "file:{}".format(log), "level": "DEBUG"},
            ]
        )
        bootstrap.ztps.set_node_check_response()

        text_onstart = random_string()
        text_onsuccess = random_string()
        text_onfailure = random_string()
        bootstrap.ztps.set_definition_response(
            actions=[
                {
                    "action": "startup_config_action",
                    "onstart": text_onstart,
                    "onsuccess": text_onsuccess,
                    "onfailure": text_onfailure,
                }
            ]
        )
        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())
        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.eapi_node_information_collected())
            self.assertTrue(bootstrap.success())
            self.assertFalse(bootstrap.error)
            log = "".join(file_log(log))
            self.assertTrue("startup_config_action: {}".format(text_onstart) in log)
            self.assertTrue("startup_config_action: {}".format(text_onsuccess) in log)
            self.assertTrue("startup_config_action: {}".format(text_onfailure) not in log)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
