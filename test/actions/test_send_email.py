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

import unittest
from test.client.client_test_lib import (
    ActionFailureTest,
    Bootstrap,
    get_action,
    raise_exception,
    random_string,
    startup_config_action,
)

import six

if six.PY2:
    from test.client.smtp_server2 import SmtpServer
else:
    from test.client.smtp_server3 import SmtpServer


class FailureTest(ActionFailureTest):
    def test_missing_smarthost(self):
        self.basic_test("send_email", "Missing attribute('smarthost')")

    def test_missing_sender(self):
        self.basic_test(
            "send_email", "Missing attribute('sender')", attributes={"smarthost": random_string()}
        )

    def test_missing_receivers(self):
        self.basic_test(
            "send_email",
            "Missing attribute('receivers')",
            attributes={"smarthost": random_string(), "sender": random_string()},
        )


class SuccessTest(unittest.TestCase):
    def setUp(self):
        self.smtp_server = SmtpServer()
        self.smtp_server.start()

    def tearDown(self):
        self.smtp_server.stop()

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        bootstrap.ztps.set_definition_response(
            actions=[
                {"action": "startup_config_action"},
                {
                    "action": "test_action",
                    "attributes": {
                        "smarthost": "{}:{}".format(
                            self.smtp_server.hostname, self.smtp_server.port
                        ),
                        "sender": "ztps@localhost",
                        "receivers": ["ztps@localhost"],
                    },
                },
            ]
        )

        bootstrap.ztps.set_action_response("startup_config_action", startup_config_action())

        action = get_action("send_email")
        bootstrap.ztps.set_action_response("test_action", action)

        bootstrap.start_test()
        try:
            self.assertTrue(bootstrap.success())
        except Exception as exception:  # pylint: disable=W0703
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(exception)
        finally:
            bootstrap.end_test()


if __name__ == "__main__":
    unittest.main()
