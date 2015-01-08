.. _tv-reference-label:

Topology Validation
===================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Enable/Disable Topology Validation
----------------------------------

Objective
^^^^^^^^^

Topology Validation uses LLDP Neighbor information to make sure you have everything
wired up correctly. Topology Validation is enabled/disabled in the main ``ztpserver.conf``
configuration file.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: shell

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``disable_topology_validation``

.. code-block:: shell

  # To disable Topology Validation
  disable_topology_validation = True

  #To enable Topology Validation
  disable_topology_validation = False

Restart the ztps process:

.. code-block:: shell

  # If using Apache WSGI
  admin@ztpserver:~# service apache2 restart

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps

Explanation
^^^^^^^^^^^

This configuration option enables/disables Topology Validation. This feature
is extremely powerful and can help you confirm all of your nodes are wired up
correctly. See the recipes below to learn more about the flexibility of
Topology Validation.

.. End of Enable/Disable Topology Validation
