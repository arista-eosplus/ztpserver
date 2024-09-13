.. _client-logging-label:

Client-Side Logging
===================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Configure Syslog Logging
------------------------

Objective
^^^^^^^^^

I want to send client logs to a syslog server or a local file during provisioning.

Solution
^^^^^^^^

.. code-block:: console

  # Edit the bootstrap configuration file
  admin@ztpserver:~# vi /usr/share/ztpserver/bootstrap/bootstrap.conf

Add any syslog servers or files, be sure to choose the level of logging:

.. code-block:: yaml

  ---
  logging:
    -
      destination: <SYSLOG-URL>:<PORT>
      level: DEBUG
    -
      destination: file:/tmp/ztps-log
      level: INFO

Explanation
^^^^^^^^^^^

The node will request the contents of the ``bootstrap.conf`` when it performs
``GET /bootstrap/config``. Once the node retrieves this information it will
send logs to the ``destination(s):`` listed under ``logging:``.

.. End of Configure Syslog Logging
