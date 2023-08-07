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
import json
import os
import random
import re
import shutil
import string
import subprocess
import time
import unittest
from collections import namedtuple

from six import ensure_binary, ensure_str, ensure_text, raise_from
from six.moves import _thread
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# pylint: disable=C0103
Response = namedtuple("Response", "content_type status contents headers")
# pylint: enable=C0103

RC_EOS = "rc.eos"
BOOT_EXTENSIONS = "boot-extensions"
BOOT_EXTENSIONS_FOLDER = ".extensions"
STARTUP_CONFIG = "startup-config"
ZTP_PLUGINS_FOLDER = ".ztp-plugins"

ZTPS_SERVER = "127.0.0.1"
ZTPS_PORT = 12345

EAPI_SERVER = "127.0.0.1"
EAPI_PORT = 1080

BOOTSTRAP_FILE = "client/bootstrap"

CLI_LOG = "/tmp/FastCli-log"
EAPI_LOG = "/tmp/eapi-log-{}".format(os.getpid())

STATUS_OK = 200
STATUS_CREATED = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_CONFLICT = 409

SYSTEM_MAC = "1234567890"


def raise_exception(exception):
    # pylint: disable=C0301, C0321

    # Uncomment the following line for debugging
    # import pdb; pdb.set_trace()

    raise_from(
        RuntimeError(
            "{}\nUncomment line in client_test_lib.py:raise_exception for debugging".format(
                exception
            )
        ),
        exception,
    )


ztps = None  # pylint: disable=C0103


def start_ztp_server():
    global ztps  # pylint: disable=W0603
    if not ztps:
        ztps = ZTPServer()
        ztps.start()
    else:
        ztps.cleanup()
    return ztps


eapis = None  # pylint: disable=C0103


def start_eapi_server():
    global eapis  # pylint: disable=W0603
    if not eapis:
        eapis = EAPIServer()
        eapis.start()
    else:
        eapis.cleanup()
    return eapis


def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def clear_cli_log():
    remove_file(CLI_LOG)


def clear_eapi_log():
    remove_file(EAPI_LOG)


def clear_logs():
    clear_cli_log()
    clear_eapi_log()


def eapi_log():
    try:
        with io.open(EAPI_LOG, encoding="utf8") as fd:
            return [x.strip() for x in fd.readlines()]
    except OSError:
        return []


def cli_log():
    try:
        with io.open(CLI_LOG, encoding="utf8") as fd:
            return [x.strip().split("-c ")[-1] for x in fd.readlines()]
    except OSError:
        return []


def file_log(filename, ignore_string=None):
    try:
        with io.open(filename, encoding="utf8") as fd:
            lines = [x.strip() for x in fd.readlines()]
        if ignore_string:
            return [y for y in lines if y and ignore_string not in y]
        return [y for y in lines if y]
    except OSError:
        return []


def get_action(action):
    with io.open("actions/{}".format(action), encoding="utf8") as fd:
        return fd.read()


def startup_config_action(lines=None):
    startup_config = "/tmp/ztps-flash-{}/startup-config".format(os.getpid())
    if not lines:
        lines = ["test"]

    user = os.getenv("USER")
    return """#!/usr/bin/env python
import os
import pwd

def main(attributes):
   user = pwd.getpwnam('{user}').pw_uid
   group = pwd.getpwnam('{user}').pw_gid

   f = open('{startup_config}', 'w')
   f.write(\'\'\'{}\'\'\')
   f.close()

   os.chmod('{startup_config}', 0o777)
   os.chown('{startup_config}', user, group)
""".format(
        "\n".join(lines),
        user=user,
        startup_config=startup_config,
    )


def print_action(msg="TEST", use_attribute=False, create_copy=False):
    # pylint: disable=E0602
    if use_attribute and create_copy:
        return """#!/usr/bin/env python

def main(attributes):
   attrs = attributes.copy()
   print(attrs.get('print_action-attr'))
"""

    if use_attribute:
        return """#!/usr/bin/env python

def main(attributes):
   print(attributes.get('print_action-attr'))
"""

    return """#!/usr/bin/env python

def main(attributes):
   print('{}')
""".format(
        msg
    )


def print_attributes_action(attributes):
    # pylint: disable=E0602
    result = """#!/usr/bin/env python

def main(attributes):
"""
    result += "\n".join("    print(attributes.get('{}')".format(attr) for attr in attributes)
    return result


def fail_flash_file_action(flash, filename):
    """Creates file on flash and then fails"""

    return """#!/usr/bin/env python

def main(attributes):
   open('{}/{}', 'w').write('test')
   raise Exception('Ops! I failed! :(')
""".format(
        flash, filename
    )


def fail_action():
    return """#!/usr/bin/env python

def main(attributes):
   raise Exception('Ops! I failed! :(')
"""


def erroneous_action():
    return """THIS_IS_NOT_PYTHON"""


def missing_main_action():
    return """#!/usr/bin/env python"""


def wrong_signature_action():
    return """#!/usr/bin/env python

def main():
   pass
"""


def exception_action():
    return """#!/usr/bin/env python

def main(attributes):
   raise Exception
"""


def random_string():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(3, 20))
    )


class Bootstrap:
    def __init__(self, server=None, eapi_port=None, ztps_default_config=False):
        os.environ["PATH"] += ":{}/test/client".format(os.getcwd())

        self.server = server if server else "{}:{}".format(ZTPS_SERVER, ZTPS_PORT)
        self.eapi_port = eapi_port if eapi_port else EAPI_PORT

        self.output = None
        self.error = None
        self.return_code = None
        self.filename = None
        self.module = None

        self.eapi = start_eapi_server()
        self.ztps = start_ztp_server()

        self.flash = "/tmp/ztps-flash-{}".format(os.getpid())
        self.temp = "/tmp/ztps-tmp-{}".format(os.getpid())

        self.rc_eos = "{}/{}".format(self.flash, RC_EOS)
        self.boot_extensions = "{}/{}".format(self.flash, BOOT_EXTENSIONS)
        self.boot_extensions_folder = "{}/{}".format(self.flash, BOOT_EXTENSIONS_FOLDER)
        self.ztp_plugins_folder = os.path.join(self.flash, ZTP_PLUGINS_FOLDER)
        self.startup_config = "{}/{}".format(self.flash, STARTUP_CONFIG)

        self.configure()

        if ztps_default_config:
            self.ztps.set_config_response()
            self.ztps.set_node_check_response()

    def configure(self):
        for folder in [self.flash, self.temp]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        self.filename = "/tmp/bootstrap-{}".format(os.getpid())
        with io.open(BOOTSTRAP_FILE, encoding="utf8") as infile, io.open(
            self.filename, "w", encoding="utf8"
        ) as outfile:
            for line in infile:
                line = line.replace("$SERVER", "http://{}".format(self.server))
                line = line.replace(
                    'COMMAND_API_SERVER = "localhost"',
                    'COMMAND_API_SERVER = "localhost:{}"'.format(self.eapi_port),
                )

                line = line.replace('FLASH = "/mnt/flash"', 'FLASH = "{}"'.format(self.flash))

                line = line.replace('TEMP = "/tmp"', 'TEMP = "{}"'.format(self.temp))

                # Reduce HTTP timeout
                if re.match("^HTTP_TIMEOUT", line):
                    line = "HTTP_TIMEOUT = 0.01"

                outfile.write(ensure_text(line))

        os.chmod(self.filename, 0o777)

    def end_test(self):
        shutil.rmtree(self.temp)
        shutil.rmtree(self.flash)

        # Clean up actions
        for url in self.ztps.responses:
            filename = url.split("/")[-1]
            remove_file("/tmp/{}".format(filename))
            remove_file("/tmp/{}c".format(filename))

        # Clean up log files
        for filename in os.listdir("/tmp"):
            if re.search("^ztps-log-", filename):
                os.remove(os.path.join("/tmp", filename))

        # Clean up bootstrap script
        remove_file(self.filename)
        remove_file("{}c".format(self.filename))

        # Clean up logs
        clear_logs()

    def start_test(self):
        try:
            proc = subprocess.Popen(  # pylint: disable=R1732
                [self.filename],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (output, error) = proc.communicate()
            self.output, self.error = ensure_str(output), ensure_str(error)
            self.return_code = proc.returncode
        finally:
            os.remove(self.filename)

    def node_information_collected(self):
        cmds = ["show version", "show lldp neighbors"]  # Collect system MAC for logging
        return [x for x in eapi_log() if x != "enable"][-2:] == cmds

    def eapi_configured(self):
        cmds = [
            "configure",
            "username ztps secret ztps-password privilege 15",
            "management api http-commands",
            "no protocol https",
            "protocol http",
            "no shutdown",
        ]
        return cli_log()[:6] == cmds

    def eapi_node_information_collected(self):
        return self.eapi_configured() and self.node_information_collected()

    def server_connection_failure(self):
        return (
            "server connection error" in self.output or "Read timed out" in self.output
        ) and self.return_code

    def eapi_failure(self):
        return "unable to enable eAPI" in self.output and self.return_code

    def unexpected_response_failure(self):
        return "unexpected response from server" in self.output and self.return_code

    def node_not_found_failure(self):
        return "node not found on server" in self.output and self.return_code

    def toplogy_check_failure(self):
        return "server-side topology check failed" in self.output and self.return_code

    def action_not_found_failure(self):
        return "action not found on server" in self.output and self.return_code

    def missing_startup_config_failure(self):
        return "startup configuration is missing" in self.output and self.return_code

    def action_failure(self):
        return "executing action failed" in self.output and self.return_code

    def invalid_definition_format(self):
        return "section missing from definition" in self.output and self.return_code

    def invalid_definition_location_failure(self):
        return (
            "invalid definition location received from server" in self.output and self.return_code
        )

    def success(self):
        return "ZTP bootstrap completed successfully!" in self.output and not self.return_code


class EAPIServer:
    # pylint: disable=C0103,E0213,W0201

    def __init__(self, mac=SYSTEM_MAC, model="", serial_number="", version=""):
        self.mac = mac
        self.model = model
        self.serial_number = serial_number
        self.version = version

        self.fail_commands = []

    def cleanup(self):
        self.responses = {}

    def add_failing_command(self, cmd):
        self.fail_commands += [cmd]

    def start(self):
        _thread.start_new_thread(self._run, ())

    def _run(self):
        class EAPIHandler(BaseHTTPRequestHandler):
            def do_POST(req):
                request = req.rfile.read(int(req.headers.get("content-length")))
                cmds = [x for x in json.loads(request)["params"][1] if x]
                if cmds:
                    with open(EAPI_LOG, "a+b") as fd:
                        fd.write(ensure_binary("%s\n" % "\n".join(cmds), "utf8"))

                print("EAPIServer: responding to request:{} ({})".format(req.path, ", ".join(cmds)))

                if [x for x in cmds if x in self.fail_commands]:
                    print("EAPIServer: failed on-demand")
                    req.send_response(STATUS_BAD_REQUEST)
                    return

                req.send_response(STATUS_OK)

                if req.path == "/command-api":
                    req.send_header("Content-type", "application/json")
                    req.end_headers()
                    if cmds == ["enable", "show version"]:
                        req.wfile.write(
                            ensure_binary(
                                json.dumps(
                                    {
                                        "result": [
                                            {},
                                            {
                                                "modelName": self.model,
                                                "version": self.version,
                                                "serialNumber": self.serial_number,
                                                "systemMacAddress": self.mac,
                                            },
                                        ]
                                    }
                                ),
                                "utf8",
                            )
                        )
                    elif cmds == ["enable", "show lldp neighbors"]:
                        req.wfile.write(
                            ensure_binary(
                                json.dumps({"result": [{}, {"lldpNeighbors": []}]}), "utf8"
                            )
                        )
                    else:
                        req.wfile.write(ensure_binary(json.dumps({"result": [{}]}), "utf8"))
                    print("EAPIServer: RESPONSE: [{}]")
                else:
                    print("EAPIServer: No RESPONSE")

        server_class = HTTPServer
        httpd = server_class((EAPI_SERVER, EAPI_PORT), EAPIHandler)
        print(time.asctime(), "EAPIServer: Server starts - {}:{}".format(EAPI_SERVER, EAPI_PORT))

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
            print(time.asctime(), "EAPIServer: Server stops - {}:{}".format(EAPI_SERVER, EAPI_PORT))


class ZTPServer:
    # pylint: disable=C0103,,E0213

    # { <URL>: ( <CONTNENT-TYPE>, <STATUS>, <RESPONSE> ) }
    responses = {}

    def cleanup(self):
        self.responses = {}

    def set_file_response(self, filename, output, content_type="text/plain", status=STATUS_OK):
        self.responses["/{}".format(filename)] = Response(content_type, status, output, {})

        meta = {"size": len(output)}
        self.responses["/meta/{}".format(filename)] = Response(
            "application/json", 200, json.dumps(meta), {}
        )

    def set_action_response(self, action, output, content_type="text/x-python", status=STATUS_OK):
        self.responses["/actions/{}".format(action)] = Response(content_type, status, output, {})

    def set_config_response(
        self, logging=None, xmpp=None, content_type="application/json", status=STATUS_OK
    ):
        response = {"logging": [], "xmpp": {}}
        if logging:
            response["logging"] = logging

        if xmpp:
            response["xmpp"] = xmpp

        self.responses["/bootstrap/config"] = Response(
            content_type, status, json.dumps(response), {}
        )

    def set_node_check_response(self, content_type="text/html", status=None, location=None):
        if status is None:
            status = random.choice([STATUS_CONFLICT, STATUS_CREATED])

        headers = {}
        if location:
            headers["location"] = location

        self.responses["/nodes"] = Response(content_type, status, "", headers)

    def set_bogus_definition_response(self):
        self.responses["/nodes/{}".format(SYSTEM_MAC)] = Response(
            "application/json", STATUS_OK, json.dumps({}), {}
        )

    def set_definition_response(
        self,
        node_id=SYSTEM_MAC,
        name="DEFAULT_DEFINITION",
        actions=None,
        content_type="application/json",
        status=STATUS_OK,
    ):
        response = {
            "name": name,
            "actions": [],
        }
        if actions:
            response["actions"] += actions

        self.responses["/nodes/{}".format(node_id)] = Response(
            content_type, status, json.dumps(response), {}
        )

    def start(self):
        _thread.start_new_thread(self._run, ())

    def _run(self):
        class ZTPSHandler(BaseHTTPRequestHandler):
            @classmethod
            def do_request(cls, req):
                if req.path in self.responses:
                    response = self.responses[req.path]
                    req.send_response(response.status)
                    req.error_content_type = response.content_type

                    req.send_header("Content-type", response.content_type)
                    for name, value in response.headers.items():
                        req.send_header(name, value)

                    req.end_headers()
                    req.wfile.write(ensure_binary(response.contents, "utf8"))
                    print(
                        "ZTPS: RESPONSE: (ct={}, status={}, output={}...)".format(
                            response[0], response[1], response[2][:100]
                        )
                    )
                else:
                    print("ZTPS: No RESPONSE")

            def do_GET(req):
                print("ZTPS: responding to GET request:{}".format(req.path))
                ZTPSHandler.do_request(req)

            def do_POST(req):
                print("ZTPS: responding to POST request:{}".format(req.path))
                headers = self.responses["/nodes"].headers
                if "location" not in headers:
                    length = req.headers.get("content-length")
                    node_id = json.loads(req.rfile.read(int(length)))["systemmac"]
                    location = "http://{}:{}/nodes/{}".format(ZTPS_SERVER, ZTPS_PORT, node_id)
                    self.responses["/nodes"].headers["location"] = location

                ZTPSHandler.do_request(req)

        server_class = HTTPServer
        httpd = server_class((ZTPS_SERVER, ZTPS_PORT), ZTPSHandler)

        print(time.asctime(), "ZTPS: Server starts - {}:{}".format(ZTPS_SERVER, ZTPS_PORT))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
            print(time.asctime(), "ZTPS: Server stops - {}:{}".format(ZTPS_SERVER, ZTPS_PORT))


class ActionFailureTest(unittest.TestCase):
    # pylint: disable=R0904

    def basic_test(
        self, action, return_string, attributes=None, action_value=None, file_responses=None
    ):
        if not attributes:
            attributes = {}

        if not file_responses:
            file_responses = {}

        if not action_value:
            action_value = get_action(action)

        bootstrap = Bootstrap(ztps_default_config=True)
        action_value = (
            action_value.replace("/mnt/flash/.extensions", bootstrap.boot_extensions_folder)
            .replace("/mnt/flash/boot-extensions", bootstrap.boot_extensions)
            .replace("/mnt/flash/.ztp-plugins", bootstrap.ztp_plugins_folder)
        )
        bootstrap.ztps.set_definition_response(
            actions=[{"action": "test_action", "attributes": attributes}]
        )
        bootstrap.ztps.set_action_response("test_action", action_value)

        for key, value in file_responses.items():
            bootstrap.ztps.set_file_response(key, value)

        bootstrap.start_test()

        try:
            self.assertTrue(bootstrap.action_failure())
            self.assertTrue(return_string in bootstrap.output)
        except AssertionError as assertion:
            print("Output: {}".format(bootstrap.output))
            print("Error: {}".format(bootstrap.error))
            raise_exception(assertion)
        finally:
            bootstrap.end_test()
