Provision a Dynamic Node
========================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Using Open Patterns
-------------------

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

.. End of Using Open Patterns


Identify a Node Based Upon Specific Neighbor
--------------------------------------------

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



Identify a Node’s Neighbors Using Regex
---------------------------------------

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

.. End of Identify a Node Based Upon Specific Neighbor
