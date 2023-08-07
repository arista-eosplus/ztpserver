#
# Copyright (c) 2023, Arista Networks, Inc.
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

# pylint: disable=C0209,W4901,E0401

import asyncore
import smtpd
import threading
import time

SMTP_SERVER = "127.0.0.1"
SMTP_PORT = 2525


class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        pass


class SmtpServer:
    def __init__(self, hostname=SMTP_SERVER, port=SMTP_PORT):
        self.hostname = hostname
        self.port = port
        self.smtp = None
        self.thread = None

    def start(self):
        """Start the listening service"""
        print("{} SMTP: Server starts - {}:{}".format(time.asctime(), self.hostname, self.port))
        self.smtp = CustomSMTPServer((self.hostname, self.port), None)
        self.thread = threading.Thread(target=asyncore.loop, kwargs={"timeout": 1})
        self.thread.start()

    def stop(self):
        """Stop listening now to port 25"""
        self.smtp.close()
        self.thread.join()
        print("{} SMTPS: Server stops - {}:{}".format(time.asctime(), self.hostname, self.port))
