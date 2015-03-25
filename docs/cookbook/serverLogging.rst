Server-Side Logging
===================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Standalone - Redirect Output to file
------------------------------------

Objective
^^^^^^^^^

When running the ZTPServer in Standalone Mode, the logs just fill up my console
so I'd like to be able to redirect the output to a file.

Solution
^^^^^^^^

With INFO level logging:

.. code-block:: console

  admin@ztpserver:~# ztps >~/ztps-console.log 2>&1 &

With DEBUG level logging:

.. code-block:: console

  admin@ztpserver:~# ztps --debug >~/ztps-console.log 2>&1 &

Explanation
^^^^^^^^^^^

Here we invoke the ztps process as usual, however we redirect the stdout messages
to a predefined file. Of course, be sure that you have permission to write
to the file you have listed.

.. End of Standalone - Redirect Output to file


Apache - View Standard Logs
---------------------------

Objective
^^^^^^^^^

I'm running the ZTPServer as a WSGI under Apache, so where do the logs go?

Solution
^^^^^^^^

Typically, you can see each transaction in:

.. code-block:: console

  # Ubuntu
  admin@ztpserver:~# more /var/log/apache2/access.log

  # Fedora
  admin@ztpserver:~# more /var/log/httpd/access_log

And the ZTPServer logs will be in:

.. code-block:: console

  # Ubuntu
  admin@ztpserver:~# more /var/log/apache2/error.log

  # Fedora
  admin@ztpserver:~# more /var/log/httpd/error_log

Explanation
^^^^^^^^^^^

These locations are the default on most standard Apache installs. It might be
misleading, but all levels of ZTPServer logging will end up as an Apache error.

**Example**

.. code-block:: console

  [Fri Dec 12 10:49:42.186976 2014] [:error] [pid 864] INFO: [app:115] Logging started for ztpserver
  [Fri Dec 12 10:49:42.187112 2014] [:error] [pid 864] INFO: [app:116] Using repository /usr/share/ztpserver

.. End of Apache - View Standard Logs
