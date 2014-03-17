#!/usr/bin/env python 
#
# Copyright (c) 2014, Arista Networks, Inc.
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

import imp
import json
import re
import os
import pdb
import random
import subprocess
import string                        #pylint: disable=W0402
import time
import thread

import BaseHTTPServer

ZTPS_SERVER = '127.0.0.1'
ZTPS_PORT = 12345

EAPI_SERVER = '127.0.0.1'
EAPI_PORT = 1080

BOOTSTRAP_FILE = 'client/bootstrap'

CLI_LOG = '/tmp/FastCli-log'
EAPI_LOG = '/tmp/eapi-log-%s' % os.getpid()

STARTUP_CONFIG = '/tmp/startup-config-%s' % os.getpid()

STATUS_OK = 200
STATUS_CREATED = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_CONFLICT = 409

SYSTEM_MAC = '1234567890'

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
    clear_startup_config()
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
    user = os.getenv('USER')
    return '''#!/usr/bin/env python
import os
import pwd

def main( attributes ):
   user = pwd.getpwnam('%s').pw_uid
   group = pwd.getpwnam('%s').pw_gid

   f = file('%s', 'w')
   f.write('test')
   f.close()

   os.chmod('%s', 0777)
   os.chown('%s', user, group)
''' % (user, user,
       STARTUP_CONFIG, STARTUP_CONFIG, STARTUP_CONFIG)

def print_action(msg='TEST', use_attribute=False):
    #pylint: disable=E0602
    if use_attribute:
        return '''#!/usr/bin/env python

def main(attributes):
   print attributes['print_action']
'''
    
    return '''#!/usr/bin/env python

def main(attributes):
   print '%s'
''' % msg

def fail_action():
    return '''#!/usr/bin/env python

def main(attributes):
   return 2
'''

def erroneous_action():
    return '''THIS_IS_NOT_PYTHON'''

def missing_main_action():
    return '''#!/usr/bin/env python'''

def wrong_signature_action():
    return '''#!/usr/bin/env python

def main():
   pass
'''

def exception_action():
    return '''#!/usr/bin/env python

def main(attributes):
   raise Exception
'''

def random_string():
    return ''.join(random.choice(
            string.ascii_uppercase + 
            string.digits) for _ in range(random.randint(10,100)))


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

    def end_test(self, clean_files=None):
        # Clean up actions
        if not clean_files:
            clean_files = []
            
        for filename in clean_files:
            remove_file('/tmp/%s' % filename)
            remove_file('/tmp/%sc' % filename)

        # Clean up log files
        for filename in os.listdir('/tmp'):
            if re.search('^ztps-log-', filename):
                os.remove(os.path.join('/tmp', filename))
                
        # Clean up bootstrap script
        remove_file(self.filename)
        remove_file('%sc' % self.filename)
                
        # Clean up logs
        clear_logs()

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

    def unexpected_response_failure(self):
        return self.return_code == 3

    def node_not_found_failure(self):
        return self.return_code == 4

    def toplogy_check_failure(self):
        return self.return_code == 5

    def action_not_found_failure(self):
        return self.return_code == 6

    def missing_startup_config_failure(self):
        return self.return_code == 7

    def action_failure(self):
        return self.return_code == 8

    def success(self):
        return self.return_code == 0


class EAPIServer(object):
    #pylint: disable=C0103,E0213,W0201

    def cleanup(self):
        self.responses = {}

    def start(self):
        thread.start_new_thread(self._run, ())

    def _run(self):

        class EAPIHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_POST(req):
                request = req.rfile.read(int(req.headers.getheader(
                            'content-length')))
                cmds = [x for x in json.loads(request)['params'][1] if x]
                if cmds:
                    open(EAPI_LOG, 'a+b').write('%s\n' % '\n'.join(cmds))

                print 'EAPIServer: responding to request:%s (%s)' % ( 
                    req.path, ', '.join(cmds))

                req.send_response(STATUS_OK)

                if req.path == '/command-api':
                    req.send_header('Content-type', 'application/json')
                    req.end_headers()
                    if cmds == ['show version']:
                        req.wfile.write(json.dumps({'result' : 
                                                  [{'modelName' : '',
                                                    'internalVersion' : '',
                                                    'serialNumber' : '',
                                                    'systemMacAddress' : 
                                                    SYSTEM_MAC}]}))
                    elif cmds == ['show lldp neighbors']:
                        req.wfile.write(json.dumps({'result' : 
                                                  [{'lldpNeighbors': []}]}))
                    else:
                        req.wfile.write(json.dumps({'result' : []}))
                    print 'EAPIServer: RESPONSE: {}'
                else:
                    print 'EAPIServer: No RESPONSE'

        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((EAPI_SERVER, EAPI_PORT), EAPIHandler)
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

    # { <URL>: ( <CONTNENT-TYPE>, <STATUS>, <RESPONSE> ) }
    responses = {}

    def cleanup(self):
        self.responses = {}

    def set_response(self, url, content_type, status, output):
        self.responses[url] = (content_type, status, output)

    def set_action_response(self, action, output,
                            content_type='text/x-python',
                            status=STATUS_OK):
        self.responses['/actions/%s' % action ] = (content_type, 
                                                   status, 
                                                   output)

    def set_config_response(self, logging=None, xmpp=None,
                            content_type='application/json',
                            status=STATUS_OK):
        response = { 'logging': [],
                     'xmpp': {}
                     }
        if logging:
            response['logging'] = logging

        if xmpp:
            response['xmpp'] = xmpp
            
        self.responses['/bootstrap/config'] = (content_type, status,
                                               json.dumps(response))

    def set_node_check_response(self, content_type='text/html',
                                status=None):
        if status is None:
            status = random.choice([STATUS_CONFLICT, 
                                    STATUS_CREATED])

        self.responses['/nodes'] = (content_type, status, '')        

    def set_definition_response(self, node_id=SYSTEM_MAC,
                                name='DEFAULT_DEFINITION',
                                actions=None, attributes=None,
                                content_type='application/json',
                                status=STATUS_OK):
        response = { 'name': name,
                     'actions': {},
                     'attributes': {}
                     }
        if actions:
            response['actions'] = actions

        if attributes:
            response['attributes'] = attributes


        self.responses['/nodes/%s' % node_id] = (content_type, status,
                                                 json.dumps(response))

    def start(self):
        thread.start_new_thread(self._run, ())

    def _run(self):

        class ZTPSHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            @classmethod
            def do_request(cls, req):
                if req.path in self.responses:
                    # if self.responses[req.path][1] == STATUS_OK:
                    #     req.send_response(self.responses[req.path][1])
                    # else:
                    #     req.send_error(self.responses[req.path][1]) 

                    req.send_response(self.responses[req.path][1])
                    req.error_content_type = self.responses[req.path][0]

                    req.send_header('Content-type', self.responses[req.path][0])
                    req.end_headers()
                    req.wfile.write(self.responses[req.path][2])
                    print 'ZTPS: RESPONSE: (ct=%s, status=%s, output=%s)' % (
                        self.responses[req.path][0], 
                        self.responses[req.path][1], 
                        self.responses[req.path][2])
                else:
                    print 'ZTPS: No RESPONSE'

            def do_GET(req):
                print 'ZTPS: responding to GET request:%s' % req.path
                ZTPSHandler.do_request(req)

            def do_POST(req):
                print 'ZTPS: responding to POST request:%s' % req.path
                print self.responses
                ZTPSHandler.do_request(req)

        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((ZTPS_SERVER, ZTPS_PORT), ZTPSHandler)
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
