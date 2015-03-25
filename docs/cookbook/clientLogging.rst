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


Configure XMPP Logging
------------------------

Objective
^^^^^^^^^

I want to send client logs to specific XMPP server rooms.

Solution
^^^^^^^^

.. code-block:: console

  # Edit the bootstrap configuration file
  admin@ztpserver:~# vi /usr/share/ztpserver/bootstrap/bootstrap.conf

Add any XMPP servers and associated rooms:

.. code-block:: yaml

  ---
  xmpp:
    domain: <XMPP-SERVER-URL>
    username: bootstrap
    password: eosplus
    rooms:
      - ztps
      - devops
      - admins

Explanation
^^^^^^^^^^^

The node will request the contents of the ``bootstrap.conf`` when it performs
``GET /bootstrap/config`` file and try to join the rooms listed with the
credentials provided. Typically when joining a room, you would use a string
like, ``ztps@conference.xmpp-server.example.com``. Be sure to just provide the
``domain: xmpp-server.example.com`` leaving out the ``conference`` prefix.

.. note:: In order for XMPP logging to work, a non-EOS user need to be connected
          to the room specified in bootstrap.conf, before the ZTP process starts.
          The room has to be created (by the non-EOS user) before the bootstrap
          client starts logging the ZTP process via XMPP.

.. End of Configure XMPP Logging
