#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#pylint: disable=R0904

import unittest

from ClientTestLib import debug    #pylint: disable=W0611
from ClientTestLib import Bootstrap, EAPIServer, ZTPServer

class BasicTest(unittest.TestCase):
    
    def test_server_not_running(self):
        test = Bootstrap()

        test.run()
        self.assertTrue(test.server_connection_failure())
        print test.output

class EAPIErrorTest(unittest.TestCase):

    def test_eapi_error(self):
        test = Bootstrap()

        ztps = ZTPServer()
        ztps.start()
        ztps.set_config_response()

        test.run()
        self.assertTrue(test.eapi_failure())
        print test.output

class MissingStartupConfigTest(unittest.TestCase):

    def test_missing_startup_config(self):
        test = Bootstrap()

        ztps = ZTPServer()
        ztps.start()
        ztps.set_config_response()
        ztps.set_definition_response()

        eapi = EAPIServer()
        eapi.start()

        test.run()

        self.assertTrue(test.missing_startup_config_failure())
        print test.output
        
if __name__ == '__main__':
    unittest.main()
