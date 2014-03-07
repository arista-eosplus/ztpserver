#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#pylint: disable=R0904

import unittest

from ClientTestLib import debug    #pylint: disable=W0611
from ClientTestLib import Bootstrap
from ClientTestLib import start_eapi_server, start_ztp_server


class BasicTest(unittest.TestCase):
    
    def test_server_not_running(self):
        test = Bootstrap()

        test.run()
        self.assertTrue(test.server_connection_failure())


class EAPIErrorTest(unittest.TestCase):

    def test_eapi_error(self):
        test = Bootstrap()

        ztps = start_ztp_server()
        ztps.set_config_response()

        test.run()
        self.assertTrue(test.eapi_failure())


class MissingStartupConfigTest(unittest.TestCase):

    def test_missing_startup_config(self):
        test = Bootstrap()

        ztps = start_ztp_server()
        ztps.set_config_response()
        ztps.set_definition_response()

        eapi = start_eapi_server()
        assert eapi

        test.run()

        self.assertTrue(test.missing_startup_config_failure())

        
if __name__ == '__main__':
    unittest.main()
