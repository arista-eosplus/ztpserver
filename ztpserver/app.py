#
# Copyright (c) 2015, Arista Networks, Inc.
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

import argparse
import logging
import os
import re
import sys

from wsgiref.simple_server import make_server


from ztpserver import config, controller

from ztpserver.serializers import load, dump
from ztpserver.validators import NeighbordbValidator
from ztpserver.constants import CONTENT_TYPE_YAML
from ztpserver.topology import FUNC_RE, neighbordb_path
from ztpserver.utils import all_files
from ztpserver.resources import resource_plugins

log = logging.getLogger('ztpserver')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

def enable_handler_console(level=None):
    ''' Enables logging to stdout '''
    
    logging_fmt = config.runtime.default.console_logging_format
    formatter = logging.Formatter(logging_fmt)

    ch = logging.StreamHandler()
    ch.tag = 'console'

    
    for handler in log.handlers:
        if 'tag' in handler.__dict__ and handler.tag == ch.tag:
            # Handler previously added
            return

    level = level or 'DEBUG'
    level = str(level).upper()
    level = logging.getLevelName(level)
    ch.setLevel(level)
    ch.setFormatter(formatter)

    log.addHandler(ch)

def python_supported():
    ''' Returns True if the current version of the python runtime is valid '''
    return sys.version_info > (2, 7) and sys.version_info < (3, 0)

logging_started = False
def start_logging(debug):
    ''' reads the runtime config and starts logging if enabled '''
    global logging_started     #pylint: disable=W0603
    if logging_started:
        return

    if config.runtime.default.logging:
        if config.runtime.default.console_logging:
            enable_handler_console('DEBUG' if debug else 'INFO')

    logging_started = True

def load_config(conf=None):
    conf = conf or config.GLOBAL_CONF_FILE_PATH
    conf = os.environ.get('ZTPS_CONFIG', conf)

    if os.path.exists(conf):
        log.info('Loading config file: %s' % conf)
        config.runtime.read(conf)

def start_wsgiapp(config_file=None, debug=False):
    ''' Provides the entry point into the application for wsgi compliant
    servers.   Accepts a single keyword argument ``conf``.   The ``conf``
    keyword argument specifies the path the server configuration file.  The
    default value is /etc/ztpserver/ztpserver.conf.

    :param conf: string path pointing to configuration file
    :return: a wsgi application object

    '''
    load_config(config_file)
    start_logging(debug)

    try:
        version = open(config.VERSION_FILE_PATH).read().split()[0].strip()
    except Exception:  # pylint: disable=W0703
        version = 'N/A'

    log.info('Starting ZTPServer v%s...' % version)

    log.info('Logging started for ztpserver')
    log.info('Using repository %s', config.runtime.default.data_root)

    if not python_supported():
        raise SystemExit('ERROR: ZTPServer requires Python 2.7')

    return controller.Router()

def run_server(version, config_file, debug):
    ''' The :py:func:`run_server` is called by the main command line routine to
    run the server as standalone.   This function accepts a single argument
    that points towards the configuration file describing this server

    This function will block on the active thread until stopped.

    :param conf: string path pointing to configuration file
    '''
    app = start_wsgiapp(config_file, debug)

    host = config.runtime.server.interface
    port = config.runtime.server.port

    log.info('URL: http://%s:%s' % (host, port))

    httpd = make_server(host, port, app)

    log.info('Starting ZTPServer v%s on http://%s:%s' % 
             (version, host, port))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info('Shutdown...')

def validate_neighbordb():
    # Validating neighbordb
    validator = NeighbordbValidator('N/A')
    neighbordb = neighbordb_path()
    print 'Validating neighbordb (\'%s\')...' % neighbordb
    try:
        validator.validate(load(neighbordb, CONTENT_TYPE_YAML,
                                'validator'))
        total_patterns = len(validator.valid_patterns) + \
            len(validator.invalid_patterns)
            
        if validator.invalid_patterns:
            print '\nERROR: Failed to validate neighbordb patterns'
            print '   Invalid Patterns (count: %d/%d)' % \
                (len(validator.invalid_patterns),
                 total_patterns)
            print '   ---------------------------'
            for index, pattern in enumerate(
                sorted(validator.invalid_patterns)):
                print '   [%d] %s' % (index, pattern[1])
        else:
            print 'Ok!'            
    except Exception as exc:        #pylint: disable=W0703
        print 'ERROR: Failed to validate neighbordb\n%s' % exc

def validate_definitions():
    data_root = config.runtime.default.data_root

    print '\nValidating definitions...'

    for definition in all_files(os.path.join(data_root, 
                                             'definitions')):
        print 'Validating %s...' % definition,
        try:
            def_data = load(definition, CONTENT_TYPE_YAML,
                            'validator')

            resources = re.findall(FUNC_RE, 
                                   str(def_data))

            # Validating plugins
            plugins = resource_plugins()
            missing_plugins = set([x for (x, _) in resources 
                                   if x not in plugins])
            if missing_plugins:
                plugins_path = os.path.join(data_root, 
                                            'plugins')
                print ''
                for plugin in missing_plugins:
                    print 'ERROR: Plugin \'%s\' configured in \'%s\' ' \
                        'is missing from \'%s\'!' % \
                        (plugin, definition, plugins_path)

            # Special validation for 'allocate' plugin
            resources_path = os.path.join(data_root, 
                                          'resources')
            resource_files = [x.split('/')[-1] 
                              for x in resources_path]
            missing_resources = [x for (y, x) in resources 
                                 if x not in resource_files and
                                 y == 'allocate']
            if missing_resources:
                if not missing_plugins:
                    print ''
                for res in missing_resources:
                    print 'ERROR: Resource file \'%s\' configured in \'%s\' ' \
                        'is missing from \'%s\'!' % \
                        (res, definition, resources_path)
            else:
                print 'Ok!'
        except Exception as exc:        #pylint: disable=W0703            
            print '\nERROR: Failed to validate %s\n%s' % \
                (definition, exc)

def validate_resources(raiseException=False):
    data_root = config.runtime.default.data_root

    print '\nValidating resources...'
    for resource in all_files(os.path.join(data_root, 
                                           'resources')):
        print 'Validating %s...' % resource,
        try:
            load(resource, CONTENT_TYPE_YAML,
                 'validator')
            print 'Ok!'
        except Exception as exc:        #pylint: disable=W0703 
            print '\nERROR: Failed to validate %s\n%s' % \
                (resource, exc)
            if raiseException:
                raise exc

def validate_nodes():
    data_root = config.runtime.default.data_root

    print '\nValidating nodes...'
    for filename in [x for x in all_files(os.path.join(data_root, 
                                                       'nodes'))
                     if x.split('/')[-1] in ['definition',
                                             'pattern']]:
        print 'Validating %s...' % filename,
        try:
            load(filename, CONTENT_TYPE_YAML,
                 'validator')
            print 'Ok!'
        except Exception as exc:        #pylint: disable=W0703            
            print '\nERROR: Failed to validate %s\n%s' % \
                (filename, exc)

def clear_resources(debug):
    start_logging(debug)

    try:
        validate_resources(raiseException=True)
    except Exception:                   #pylint: disable=W0703 
        sys.exit('ERROR: Unable to clear resources because of validation error')

    data_root = config.runtime.default.data_root

    print '\nClearing resources...'
    for resource in all_files(os.path.join(data_root, 
                                           'resources')):
        print 'Clearing %s...' % resource,
        try:
            contents = load(resource, CONTENT_TYPE_YAML,
                            'clear_resource')
            for key in contents:
                contents[key] = 'None'
            dump(contents, resource, CONTENT_TYPE_YAML,
                 'clear_resource')
            print 'Ok!'            
        except Exception as exc:        #pylint: disable=W0703            
            print '\nERROR: Failed to clear %s\n%s' % \
                (resource, exc)
    
def run_validator(debug):
    start_logging(debug)

    validate_neighbordb()
    validate_definitions()
    validate_resources()
    validate_nodes()

def main():
    ''' The :py:func:`main` is the main entry point for the ztpserver if called
    from the commmand line.   When called from the command line, the server is
    running in standalone mode as opposed to using the :py:func:`application` to
    run under a python wsgi compliant server
    '''

    usage = 'ztpserver [options]'

    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument('--version', '-v',
                        action='store_true',
                        help='Displays the version information')

    parser.add_argument('--conf', '-c',
                        type=str,
                        default=config.GLOBAL_CONF_FILE_PATH,
                        help='Specifies the configuration file to use')

    parser.add_argument('--validate-config', '-V',
                        action='store_true',
                        help='Validates config files')

    parser.add_argument('--debug',
                        action='store_true',
                        help='Enables debug output to the STDOUT')

    parser.add_argument('--clear-resources', '-r',
                        action='store_true',
                        help='Clears all resource files')


    args = parser.parse_args()

    version = 'N/A'
    try:
        version = open(config.VERSION_FILE_PATH).read().split()[0].strip()
    except IOError:
        pass

    if args.version:
        print 'ZTPServer version %s' % version

    if args.validate_config:
        run_validator(args.debug)

    if args.clear_resources:
        clear_resources(args.debug)

    if args.version or args.validate_config or args.clear_resources:
        sys.exit()

    return run_server(version, args.conf, args.debug)
