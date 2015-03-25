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

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``disable_topology_validation``

.. code-block:: console

  # To disable Topology Validation
  disable_topology_validation = True

  #To enable Topology Validation
  disable_topology_validation = False

Restart the ztps process:

.. code-block:: console

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



Allow Any Neighbor
------------------

Objective
^^^^^^^^^

I want to provision a node without knowing anything about it. I just want it to
receive a default configuration.

Solution
^^^^^^^^

You can accomplish this by using neighbordb. Neighbordb contains associations
between LLDP neighbor patterns and definitions. So if we use a pattern that
matches anything, we can use it to assign a simple, default definition.

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Modify your neighbordb
  admin@ztpserver:~# vi neighbordb

Add the following lines to your definition, changing values where needed:

.. code-block:: yaml

  ---
  patterns:
    - name: Default Pattern
      definition: default
      interfaces:
        - any: any:any

If you happen to be provisioning a node in isolation and the node does not have
any neighbors, use the following pattern:

.. code-block:: yaml

  ---
  patterns:
    - name: Default Pattern
      definition: default
      interfaces:
        - none: none:none

Then add a definition to ``[data_root]/definitions/default``

.. note:: See the sections on Definitions and Actions to learn more.

Explanation
^^^^^^^^^^^

By placing this pattern in your neighbordb, the ZTPServer will allow this node
to be provisioned and will assign it the ``default`` definition. Use caution when
placing this pattern in your neighbordb as it might allow nodes to receive the
``default`` definition when you intend them to receive another pattern.

.. End of Allow Any Neighbor



Match Pattern with Exact String
-------------------------------

Objective
^^^^^^^^^

I want my node to be dynamically provisioned based upon a specific LLDP
neighbor association.

Solution
^^^^^^^^

Modify your neighbordb:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Modify your neighbordb
  admin@ztpserver:~# vi neighbordb

Then add the pattern that includes the required match.

.. code-block:: yaml

  ---
  patterns:
    - name: tora for pod1
      definition: tora
      interfaces:
        - Ethernet1: dc1-pod1-spine1:Ethernet1

This pattern says that the node being provisioned must have a connection between
its Ethernet1 and dc1-pod1-spine1's Ethernet1.

Explanation
^^^^^^^^^^^

In this recipe we use neighbordb to link a pattern with a definition. When a node
executes the bootstrap script it will send the ZTPServer some information about
itself. The ZTPServer will not find any existing directory with the node's
System-ID (System MAC or Serial Number depending upon your configuration) so it
next checks neighbordb to try and find a match. The ZTPServer will analyze
the nodes LLDP neighbors, find the match in neighbordb and then apply the ``tora``
definition.

.. End of Identify a Node Based Upon Specific Neighbor



Match Pattern Using a Regular Expression
----------------------------------------

Objective
^^^^^^^^^

I want my node to be dynamically provisioned and I'd like to match certain
neighbors using regex.

Solution
^^^^^^^^

Modify your neighbordb:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Modify your neighbordb
  admin@ztpserver:~# vi neighbordb

Then add the pattern that includes the required match.

.. code-block:: yaml

  ---
  patterns:
    - name: tora for pod1
      definition: tora
      interfaces:
        - Ethernet1: regex('dc1-pod1-spine\D+'):Ethernet1

This pattern says that the node being provisioned must have a connection between
its Ethernet1 and any dc1-pod1-spines Ethernet1.

Explanation
^^^^^^^^^^^

In this recipe we use neighbordb to link a pattern with a definition. When a node
executes the bootstrap script it will send the ZTPServer some information about
itself. The ZTPServer will not find any existing directory with the node's
System-ID (System MAC or Serial Number depending upon your configuration) so it
next checks neighbordb to try and find a match. The ZTPServer will analyze
the nodes LLDP neighbors, find the match in neighbordb and then apply the ``tora``
definition.

.. note:: There are a few different functions that you can use other than ``regex()``.
          Check out this `section <http://ztpserver.readthedocs.org/en/master/config.html#variables>`_
          to learn more.

.. End of Match Pattern Using a Regular Expression




Match Pattern That Includes a String
------------------------------------

Objective
^^^^^^^^^

I want my node to be dynamically provisioned and I'd like to match certain
neighbors as long as the neighbor hostname includes a certain string.

Solution
^^^^^^^^

Modify your neighbordb:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Modify your neighbordb
  admin@ztpserver:~# vi neighbordb

Then add the pattern that includes the required match.

.. code-block:: yaml

  ---
  patterns:
    - name: tora for pod1
      definition: tora
      interfaces:
        - Ethernet1: includes('dc1-pod1'):Ethernet1

This pattern says that the node being provisioned must have a connection between
its Ethernet1 and any hostname that includes ``dc1-pod1`` Ethernet1.

Explanation
^^^^^^^^^^^

In this recipe we use neighbordb to link a pattern with a definition. When a node
executes the bootstrap script it will send the ZTPServer some information about
itself. The ZTPServer will not find any existing directory with the node's
System-ID (System MAC or Serial Number depending upon your configuration) so it
next checks neighbordb to try and find a match. The ZTPServer will analyze
the nodes LLDP neighbors, find the match in neighbordb and then apply the ``tora``
definition.

.. End of Match pattern that includes some string




Match Pattern That Excludes a String
------------------------------------

Objective
^^^^^^^^^

I want my node to be dynamically provisioned and I'd like to match certain
neighbors as long as the neighbor hostname excludes a certain string.

Solution
^^^^^^^^

Using the ``excludes()`` function allows you to match the inverse of the
``includes()`` function.

Modify your neighbordb:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Modify your neighbordb
  admin@ztpserver:~# vi neighbordb

Then add the pattern that includes the required match.

.. code-block:: yaml

  ---
  patterns:
    - name: tora for pod1
      definition: tora
      interfaces:
        - Ethernet1: includes('dc1-pod1'):Ethernet1
        - any: excludes('spine'):Ethernet50

This pattern says that the node being provisioned must have a connection between
its Ethernet1 and any hostname that includes ``dc1-pod1`` Ethernet1.

Explanation
^^^^^^^^^^^

In this recipe we use neighbordb to link a pattern with a definition. When a node
executes the bootstrap script it will send the ZTPServer some information about
itself. The ZTPServer will not find any existing directory with the node's
System-ID (System MAC or Serial Number depending upon your configuration) so it
next checks neighbordb to try and find a match. The ZTPServer will analyze
the nodes LLDP neighbors, find the match in neighbordb and then apply the ``tora``
definition.

.. End of Match pattern that includes some string
