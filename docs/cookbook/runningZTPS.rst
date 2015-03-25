Running the ZTPServer
=====================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Standalone - Change the ZTPServer Interface
-------------------------------------------

Objective
^^^^^^^^^

I only want the ZTPServer process to listen on a specific network interface.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``interface`` in the [server] group.

.. code-block:: console

  # To listen on all interfaces
  interface = 0.0.0.0

  # To listen on a specific interface
  interface = 192.0.2.100

Restart the ztps process:

.. code-block:: console

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps &

Explanation
^^^^^^^^^^^

This recipe helps you define a specific interface for the ZTPServer to listen on.


.. note:: Be sure the ``interface`` coincides with the ``server_url`` value in
          the configuration file.

.. End of Standalone - Change the ZTPServer Interface


Standalone - Run ZTPServer on a Specific Port
---------------------------------------------

Objective
^^^^^^^^^

I want to define which port the ZTPServer listens on.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``port`` in the [server] group.

.. code-block:: console

  # Choose a port of your liking
  port = 8080

Restart the ztps process:

.. code-block:: console

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps &

Explanation
^^^^^^^^^^^

This recipe helps you define a specific port for the ZTPServer to listen on.


.. note:: Be sure the ``port`` coincides with the ``server_url`` value in
          the configuration file.

.. End of Standalone - Change the ZTPServer Port


Standalone - Run ZTPServer in a Sub-directory
---------------------------------------------

Objective
^^^^^^^^^
I don't want to run the ZTPServer at the root of my domain, I want it in a
sub-directory.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``server_url`` in the [default] group.

.. code-block:: console

  # Choose a subdirectory
  server_url = http://ztpserver:8080/not/in/root/anymore

Restart the ztps process:

.. code-block:: console

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps &

Explanation
^^^^^^^^^^^

The ``server_url`` key defines where the REST API lives. You do not need to
change any of your file locations to affect change. Simply change the key above.

.. note:: You can confirm the change by doing a simple
          ``wget http://server:port/new/directory/path/bootstrap`` to retrieve
          the bootstrap script.

.. End of Standalone - Run ZTPServer in a sub-directory


Apache - Run ZTPServer on a Specific Port
-----------------------------------------

Objective
^^^^^^^^^

I'm running ZTPServer as a WSGI with Apache and want to change what port it
listens on.

Solution
^^^^^^^^

Apache configurations can vary widely, and the ZTPServer has no control over this,
so view this simply as a suggestion.

Open up your Apache configuration file:

.. code-block:: console

  # Apache
  admin@ztpserver:~# vi /etc/apache2/sites-enabled/ztpserver.conf

  # HTTPd
  admin@ztpserver:~# vi /etc/httpd/conf.d/ztpserver.conf

Change the ``Listen`` and ``VirtualHost`` values to the desired port.

.. code-block:: apacheconf

    LoadModule wsgi_module modules/mod_wsgi.so
    Listen 8080

    <VirtualHost *:8080>

        WSGIDaemonProcess ztpserver user=www-data group=www-data threads=50
        WSGIScriptAlias / /etc/ztpserver/ztpserver.wsgi
        # Required for RHEL
        #WSGISocketPrefix /var/run/wsgi

        <Location />
            WSGIProcessGroup ztpserver
            WSGIApplicationGroup %{GLOBAL}

            # For Apache <= 2.2, use Order and Allow
            Order deny,allow
            Allow from all
            # For Apache >= 2.4, Allow is replaced by Require
            Require all granted
        </Location>

        # Override default logging locations for Apache
        #ErrorLog /path/to/ztpserver_error.log
        #CustomLog /path/to/ztpserver_access.log
    </VirtualHost>

Restart the ztps process:

.. code-block:: console

  # Restart Apache
  admin@ztpserver:~# service apache2 restart

Explanation
^^^^^^^^^^^

When you run ZTPServer as a WSGI under Apache or like server, the interface
and port that are used for listening for HTTP requests are controlled by the
web server. The config snippet above shows how this might be done with Apache,
but note that variations might arise in your own environment.

.. End of Apache - Run ZTPServer on a Specific Port


Apache - Run ZTPServer in a Sub-directory
-----------------------------------------

Objective
^^^^^^^^^

I'm running ZTPServer as a WSGI with Apache and I want to change the path that
the REST API resides.

Solution
^^^^^^^^

WSGI-compliant webserver configurations can vary widely, so here's a sample of
how this is done with Apache.

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``server_url`` in the [default] group.

.. code-block:: console

  # Choose a subdirectory
  server_url = http://ztpserver:8080/not/in/root/anymore

You might think that you have to change your Apache conf to move this to a
sub-directory, but you don't. Your config should look like the block below.
Note the ``<Location />``.

.. code-block:: apacheconf

    LoadModule wsgi_module modules/mod_wsgi.so
    Listen 8080

    <VirtualHost *:8080>

        WSGIDaemonProcess ztpserver user=www-data group=www-data threads=50
        WSGIScriptAlias / /etc/ztpserver/ztpserver.wsgi
        # Required for RHEL
        #WSGISocketPrefix /var/run/wsgi

        <Location />
            WSGIProcessGroup ztpserver
            WSGIApplicationGroup %{GLOBAL}

            # For Apache <= 2.2, use Order and Allow
            Order deny,allow
            Allow from all
            # For Apache >= 2.4, Allow is replaced by Require
            Require all granted
        </Location>

        # Override default logging locations for Apache
        #ErrorLog /path/to/ztpserver_error.log
        #CustomLog /path/to/ztpserver_access.log
    </VirtualHost>

Restart the ztps process:

.. code-block:: console

  # Restart Apache
  admin@ztpserver:~# service apache2 restart

Explanation
^^^^^^^^^^^

It might seem counter-intuitive but the Apache configuration should use the
``Location`` directive to point at root. The desired change to the path is done
by the ZTPServer ``server_url`` configuration value in ``/etc/ztpserver/ztpserver.conf``.

.. End of Apache - Run ZTPServer in a Sub-directory



Change ZTPServer File Ownership
-------------------------------

Objective
^^^^^^^^^

I'd like all of the ZTPServer provisioning files to be owned by a particular
user/group.

.. note:: This is most often needed when running the ZTPServer WSGI App and the
          apache user is unable to read/write to ``/usr/share/ztpserver``.

Solution
^^^^^^^^

.. code-block:: console

  admin@ztpserver:~# chown -R myUser:myGroup /usr/share/ztpserver
  admin@ztpserver:~# chmod -R ug+rw /usr/share/ztpserver

Explanation
^^^^^^^^^^^

The shell commands listed above set ownership and permissions for the default
data_root location ``/usr/share/ztpserver``. Be mindful that if you are running
the ZTPServer WSGI App, the mod_wsgi daemon user must be able to read/write to
these files.

.. note:: When running the ZTPServer WSGI App, you should also check the
          ownership and permission of ``/etc/ztpserver/ztpserver.wsgi``.

.. End of Change ZTPServer File Ownership


Apache - Configure SELinux Permissions
--------------------------------------

Objective
^^^^^^^^^

My server has SELinux enabled and I'd like to set the ZTPServer file type so
that Apache can read/write files in the data_root.

.. note:: This is most often needed when running the ZTPServer WSGI App and the
          apache user is unable to read/write to ``/usr/share/ztpserver``.

Solution
^^^^^^^^

.. code-block:: console

  # For Fedora - httpd
  admin@ztpserver:~# chcon -Rv --type=httpd_sys_script_rw_t /usr/share/ztpserver

  # For Ubuntu - Apache
  admin@ztpserver:~# chcon -R -h system_u:object_r:httpd_sys_script_rw_t /usr/share/ztpserver

Explanation
^^^^^^^^^^^

The shell commands listed above set the SELinux file attributes so that Apache
can read/write to the files. This is often the case since ``/usr/share/ztpserver``
is not in the normal operating directory ``/var/www/``.  Note that the commands
above are suggestions and you might consider tweaking them to suit your own
environment.

.. End of Apache - Configure SELinux Permissions
