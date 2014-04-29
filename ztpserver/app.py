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
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=C0103
#
import os
import sys
import argparse

import logging

from wsgiref.simple_server import make_server

import ztpserver.config
import ztpserver.controller
import ztpserver.neighbordb

from ztpserver import __version__ as VERSION

DEFAULT_CONF = '/etc/ztpserver/ztpserver.conf'

log = logging.getLogger("ztpserver")
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

def enable_handler_console(level='DEBUG'):
    """ Enables logging to stdout """
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch = logging.StreamHandler()
    if level is None:
        level = 'DEBUG'
    level = str(level).upper()
    level = logging.getLevelName(level)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

def start_logging():
    """ reads the runtime config and starts logging if enabled """

    if ztpserver.config.runtime.default.logging:
        if ztpserver.config.runtime.default.console_logging:
            enable_handler_console()

def start_wsgiapp(conf=None):
    """ Provides the entry point into the application for wsgi compliant
    servers.   Accepts a single keyword argument ``conf``.   The ``conf``
    keyword argument specifies the path the server configuration file.  The
    default value is /etc/ztpserver/ztpserver.conf.

    :param conf: string path pointing to configuration file
    :return: a wsgi application object

    """

    conf = conf or DEFAULT_CONF
    conf = os.environ.get('ZTPS_CONFIG', conf)

    if os.path.exists(conf):
        ztpserver.config.runtime.read(conf)

    start_logging()
    log.info('Logging started for ztpserver')

    ztpserver.neighbordb.load()
    return ztpserver.controller.Router()

def run_server(conf):
    """ The :py:func:`run_server` is called by the main command line routine to
    run the server as standalone.   This function accepts a single argument
    that points towards the configuration file describing this server

    This function will block on the active thread until stopped.

    :param conf: string path pointing to configuration file
    """

    app = start_wsgiapp(conf)

    host = ztpserver.config.runtime.server.interface
    port = ztpserver.config.runtime.server.port

    httpd = make_server(host, port, app)

    print "Starting server on http://%s:%s" % (host, port)

    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        print 'Shutdown'

def main():
    """ The :py:func:`main` is the main entry point for the ztpserver if called
    from the commmand line.   When called from the command line, the server is
    running in standalone mode as opposed to using the :py:func:`application` to
    run under a python wsgi compliant server
    """

    usage = 'ztpserver [options]'

    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument('--version', '-v',
                        action='store_true',
                        help='Displays the version information')

    parser.add_argument('--conf', '-c',
                        type=str,
                        default=DEFAULT_CONF,
                        help='Specifies the configuration file to use')

    args = parser.parse_args()
    if args.version:
        print 'ztps version %s' % VERSION
        sys.exit()

    return run_server(args.conf)




