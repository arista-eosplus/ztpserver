Startup
=======

.. contents:: :local:

**HTTP Server Deployment Options**

ZTPServer is a Python WSGI compliant application that can be deployed behind any WSGI web server or run as a standalone application.  This section provides details for configuring ZTPServer to run under various WSGI compliant web servers.  By default, ZTPServer ships with a single-threaded server that is sufficient for testing.      

Standalone server
`````````````````

To start the standalone ZTPServer, exec the ztps binary

.. code-block:: console

    [root@ztpserver ztpserver]# ztps
    INFO: [app:115] Logging started for ztpserver
    INFO: [app:116] Using repository /usr/share/ztpserver
    Starting server on http://<ip_address>:<port>


The following options may be specified when starting the ztps binary:

.. code-block:: console

    -h, --help            show this help message and exit
    --version, -v         Displays the version information
    --conf CONF, -c CONF  Specifies the configuration file to use
    --validate FILENAME   Runs a validation check on neighbordb
    --debug               Enables debug output to the STDOUT

When ZTPServer starts, it reads the path information to  neighbordb and other files from the global configuration file. Assuming that the DHCP server is serving DHCP offers which include the path to the ZTPServer bootstrap script in Option 67 and that the EOS nodes can access the bootstrap file over the network, the provisioning process should now be able to automatically start for all the nodes with no startup configuration. 

.. note:

  All other files including neighbordb and other files are loaded on-access meaning that ZTPServer does NOT require a restart to pick up changes to node / pattern configurations, etc.  However, a restart IS required to pickup changes to ztpserver.conf.

Apache (mod_wsgi)
`````````````````

If using Apache, this section provides instructions for setting up ZTPServer using mod_wsgi. This section assumes the reader is familiar with Apache and has already installed mod_wsgi. For details on how to install mod_wsgi, please see the `modwsgi Quick Installation Guide <https://code.google.com/p/modwsgi/wiki/QuickInstallationGuide>`_.

To enable ZTPServer for an Apache server, we need to add the following WSGI configuration (example)

.. code-block:: apacheconf

    LoadModule wsgi_module modules/mod_wsgi.so

    WSGIDaemonProcess ztpserver user=www-data group=www-data threads=5
    WSGIScriptAlias / /etc/ztpserver/ztpserver.wsgi
    
    <Directory /ztpserver>
        WSGIProcessGroup ztpserver
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>


WSGIScriptAlias should point to the ztpserver.wsgi file which is installed by default under /etc/ztpserver. The ``<Directory /ztpserver>`` tag assigns the path prefix for the ZTPServer url. The ZTPServer configuration must be updated to include the URL path prefix (``/ztpserver`` in this example).

To update the ZTPServer configuration, edit the default configuration file found at /etc/ztpserver/ztpserver.conf by modifying or adding the following line under the [default] section:

``server_url = http://192.168.1.34/ztpserver``

where /ztpserver is the same name as the directory entry configured above.  Once completed, restart Apache and you should now be able to access your ZTPServer at the specified URL.  To test, simply use curl - for example:

``curl http://1921.68.1.34/ztpserver/bootstrap``

If everything is configured properly, curl should be able to retrieve the bootstrap script. If there is a problem, all of the ZTPServer log messages should be available under the Apache server error logs.

