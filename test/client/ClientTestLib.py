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
import unittest

import BaseHTTPServer

ZTPS_SERVER = '127.0.0.1'
ZTPS_PORT = 12345

EAPI_SERVER = '127.0.0.1'
EAPI_PORT = 1080

BOOTSTRAP_FILE = 'client/bootstrap'

CLI_LOG = '/tmp/FastCli-log'
EAPI_LOG = '/tmp/eapi-log-%s' % os.getpid()

STARTUP_CONFIG = '/tmp/startup-config-%s' % os.getpid()

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

def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def clear_cli_log():
    remove_file(CLI_LOG)

def clear_eapi_log():
    remove_file(EAPI_LOG)

def clear_startup_config():
    remove_file(STARTUP_CONFIG)

def clear_logs():
    clear_cli_log()    
    clear_eapi_log()

def eapi_log():
    try:
        return [x.strip()
                for x in open(EAPI_LOG, 'r').readlines()]
    except IOError:
        return []

def cli_log():
    try:
        return [x.strip().split('-c ')[ -1 ] 
                for x in open(CLI_LOG, 'r').readlines()]
    except IOError:
        return []

def file_log(filename):
    try:
        return [x.strip() for x in open(filename, 'r').readlines()
                if 'SyslogManager' not in x]
    except IOError:
        return []

def startup_config_action():
    return '''#!/bin/bash
sudo touch %s
sudo chmod 644 %s
sudo chown %s %s''' % (STARTUP_CONFIG, STARTUP_CONFIG,
                       os.getenv('USER'), STARTUP_CONFIG)


class BaseTest(unittest.TestCase):
    #pylint: disable=C0103,R0201,R0904

    def tearDown(self):
        # Clean up files in /tmp
        for filename in os.listdir('/tmp'):
            if (re.search('^bootstrap-', filename) or 
                re.search('^ztps-log-', filename)) :
                os.remove(os.path.join('/tmp', filename))

        clear_logs()
        

class Bootstrap(object):
    #pylint: disable=R0201

    def __init__(self, server=None, eapi_port=None):
        os.environ['PATH'] += ':%s/test/client' % os.getcwd()

        self.server = server if server else '%s:%s' % (ZTPS_SERVER, ZTPS_PORT)
        self.eapi_port = eapi_port if eapi_port else EAPI_PORT

        self.output = None
        self.error = None
        self.return_code = None
        self.filename = None
        self.module = None

        self.eapi = start_eapi_server()
        self.ztps = start_ztp_server()

        self.configure()

    def configure(self):
        infile = open(BOOTSTRAP_FILE)
        self.filename = '/tmp/bootstrap-%s' % os.getpid()
        outfile = open(self.filename, 'w')

        for line in infile:
            line = line.replace('$SERVER', self.server)
            line = line.replace("COMMAND_API_SERVER = 'localhost'", 
                                "COMMAND_API_SERVER = 'localhost:%s'" % 
                                self.eapi_port)
            line = line.replace("STARTUP_CONFIG = '/mnt/flash/startup-config'", 
                                "STARTUP_CONFIG = '%s'" % STARTUP_CONFIG)

           # Reduce HTTP timeout
            if re.match('^HTTP_TIMEOUT', line):
                line = 'HTTP_TIMEOUT = 0.01'
                
            outfile.write(line)

        infile.close()
        outfile.close()
        
        os.chmod(self.filename, 0777)
        self.module = imp.load_source('bootstrap', self.filename)

    def end_test(self):
        clear_logs()
        remove_file(self.filename)

    def start_test(self):
        try:
            proc = subprocess.Popen(self.filename, 
                                    stdin=subprocess.PIPE, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            (self.output, self.error) = proc.communicate()
        finally:
            os.remove(self.filename)

        self.return_code = proc.returncode             #pylint: disable=E1101

    def node_information_collected(self):
        cmds = ['show version', 
                'show lldp neighbors']
        return eapi_log()[:2] == cmds

    def eapi_configured(self):
        cmds = ['configure', 
                'username ztps secret ztps-password privilege 15', 
                'management api http-commands', 
                'no protocol https', 
                'protocol http', 
                'no shutdown']
        return cli_log()[:6] == cmds

    def eapi_node_information_collected(self):
        return self.eapi_configured() and self.node_information_collected()
        
    def server_connection_failure(self):
        return self.return_code == 1

    def eapi_failure(self):
        return self.return_code == 2

    def missing_startup_config_failure(self):
        return self.return_code == 3

    def success(self):
        return self.return_code == 0


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
                cmds = [x for x in json.loads(request)['params'][1] if x]
                if cmds:
                    open(EAPI_LOG, 'a+b').write('%s\n' % '\n'.join(cmds))

                print 'EAPIServer: responding to request:%s (%s)' % ( 
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

    def set_action_response(self, action, content_type, output):
        self.responses['/actions/%s' % action ] = (content_type, output)

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
