#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import imp
import json
import re
import os
import pdb
import subprocess
import time
import thread

import BaseHTTPServer

ZTPS_SERVER = '127.0.0.1'
ZTPS_PORT = 12345

EAPI_SERVER = '127.0.0.1'
EAPI_PORT = 1080

BOOTSTRAP_FILE = 'client/bootstrap'


def debug():
    pdb.set_trace()

ztps = None    #pylint: disable=C0103
def start_ztp_server():
    global ztps     #pylint: disable=W0603
    if not ztps:
        ztps = ZTPServer()
        ztps.start()
    else:
        ztps.cleanup()
    return ztps

eapis = None    #pylint: disable=C0103
def start_eapi_server():
    global eapis    #pylint: disable=W0603
    if not eapis:
        eapis = EAPIServer()
        eapis.start()
    else:
        eapis.cleanup()
    return eapis


class Bootstrap(object):
    
    def __init__(self, server=None):
        os.environ['PATH'] += ':%s/test/client' % os.getcwd()

        self.server = server

        if not self.server:
            self.server = '%s:%s' % (ZTPS_SERVER, ZTPS_PORT)

        self.output = None
        self.error = None
        self.return_code = None
        self.filename = None
        self.module = None
        
        self.configure()

    def configure(self):
        infile = open(BOOTSTRAP_FILE)
        self.filename = '/tmp/bootstrap-%d' % os.getpid()
        outfile = open(self.filename, 'w')

        for line in infile:
            line = line.replace('$SERVER', self.server)
            line = line.replace("COMMAND_API_SERVER = 'localhost'", 
                                "COMMAND_API_SERVER = 'localhost:%s'" % 
                                EAPI_PORT)
            
           # Reduce HTTP timeout
            if re.match('^HTTP_TIMEOUT', line):
                line = 'HTTP_TIMEOUT = 0.01'
                
            outfile.write(line)

        infile.close()
        outfile.close()
        
        os.chmod(self.filename, 0777)        
        self.module = imp.load_source('bootstrap', self.filename)

    def run(self):
        try:
            proc = subprocess.Popen(self.filename, 
                                    stdin=subprocess.PIPE, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            (self.output, self.error) = proc.communicate()
        finally:
            os.remove(self.filename)

        self.return_code = proc.returncode             #pylint: disable=E1101

    def server_connection_failure(self):
        return self.return_code == 1

    def eapi_failure(self):
        return self.return_code == 2

    def missing_startup_config_failure(self):
        return self.return_code == 3


class EAPIServer(object):
    #pylint: disable=C0103,E0213,W0201

    def cleanup(self):
        self.responses = {}

    def start(self):
        thread.start_new_thread(self._run, ())

    def _run(self):

        class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_POST(req):
                request = req.rfile.read(int(req.headers.getheader(
                            'content-length')))
                cmds = json.loads(request)['params'][1]

                print 'EAPIServer: responding to request:%s(%s)' % ( 
                    req.path, ', '.join(cmds))

                req.send_response(200)

                if req.path == '/command-api':
                    req.send_header('Content-type', 'application/json')
                    req.end_headers()
                    if cmds == ['show version']:
                        req.wfile.write(json.dumps({'result' : 
                                                  [{'modelName' : '',
                                                    'internalVersion' : '',
                                                    'serialNumber' : '',
                                                    'systemMacAddress' : ''}]}))
                    elif cmds == ['show lldp neighbors']:
                        req.wfile.write(json.dumps({'result' : 
                                                  [{'lldpNeighbors': []}]}))
                    else:
                        req.wfile.write(json.dumps({'result' : []}))
                    print 'EAPIServer: RESPONSE: {}'
                else:
                    print 'EAPIServer: No RESPONSE'

        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((EAPI_SERVER, EAPI_PORT), MyHandler)
        print time.asctime(), 'EAPIServer: Server starts - %s:%s' % (
            EAPI_SERVER, EAPI_PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
            print time.asctime(), 'EAPIServer: Server stops - %s:%s' % (
                EAPI_SERVER, EAPI_PORT)


class ZTPServer(object):
    #pylint: disable=C0103,,E0213

    # { <URL>: ( <CONTNENT-TYPE>, <RESPONSE> ) }
    responses = {}

    def cleanup(self):
        self.responses = {}

    def set_response(self, url, content_type, output):
        self.responses[url] = (content_type, output)

    def set_config_response(self, logging=None, xmpp=None):
        response = { 'logging': [],
                     'xmpp': {}
                     }
        if logging:
            response['logging'] = logging

        if xmpp:
            response['xmpp'] = xmpp
            
        self.responses['/bootstrap/config'] = ('application/json', 
                                               json.dumps(response))

    def set_definition_response(self, name='DEFAULT_DEFINITION',
                               actions=None, attributes=None):
        response = { 'name': name,
                     'actions': {},
                     'attributes': {}
                     }
        if actions:
            response['actions'] = actions

        if attributes:
            response['attributes'] = attributes


        self.responses['/nodes'] = ('application/json', 
                                               json.dumps(response))

    def start(self):
        thread.start_new_thread(self._run, ())

    def _run(self):

        class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_GET(req):
                print 'ZTPS: responding to GET request:%s' % req.path
                req.send_response(200)

                if req.path in self.responses:
                    req.send_header('Content-type', self.responses[req.path][0])
                    req.end_headers()
                    req.wfile.write(self.responses[req.path][1])
                    print 'ZTPS: RESPONSE: (%s, %s)' % (
                        self.responses[req.path][0], 
                        self.responses[req.path][1])
                else:
                    print 'ZTPS: No RESPONSE'

            def do_POST(req):
                print 'ZTPS: responding to POST request:%s' % req.path
                req.send_response(200)

                if req.path in self.responses:
                    req.send_header('Content-type', self.responses[req.path][0])
                    req.end_headers()
                    req.wfile.write(self.responses[req.path][1])
                    print 'ZTPS: RESPONSE: (%s, %s)' % (
                        self.responses[req.path][0], 
                        self.responses[req.path][1])
                else:
                    print 'ZTPS: No RESPONSE'                    

        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((ZTPS_SERVER, ZTPS_PORT), MyHandler)
        print time.asctime(), 'ZTPS: Server starts - %s:%s' % (
            ZTPS_SERVER, ZTPS_PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
            print time.asctime(), 'ZTPS: Server stops - %s:%s' % (
                ZTPS_SERVER, ZTPS_PORT)
