Provision a Static Node
=======================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1


Add a Static Node Entry
-----------------------

Objective
^^^^^^^^^

I want to provision my switch based upon its System ID (System MAC Address
or Serial Number).

Solution
^^^^^^^^

Log into your (v)EOS node to get its System ID. If it's in ZTP Mode, just log in
with username ``admin``:

.. code-block:: shell

  switch-name> show version

.. note:: Note down the System ID(System MAC Address or Serial Number).

Let's create a nodes directory for this device:

.. code-block:: shell

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the nodes directory, where all node information is stored
  admin@ztpserver:~# cd nodes

  # Create a directory using the MAC Address you found earlier
  admin@ztpserver:~# mkdir <SYSTEM_ID>


Explanation
^^^^^^^^^^^

A node is considered to be statically provisioned when a directory with its
System ID is already located in the ``nodes/`` directory.

Note that the System ID can be the node's System MAC Address or its Serial Number.

Just adding this directory is not enough to provision the node. The remaining
recipes will finish off the task.  To successfully provision a node
statically, you will need to create:

* ``startup-config``
* ``pattern`` file - if Topology Validation is enabled
* ``definition`` - if you choose to apply other actions during provisioning

and place them in ``[data_root]/nodes/<SYSTEM_ID>``.

.. note:: Confirm your ZTPServer Configuration will identify a node based upon
          the desired System ID by checking /etc/ztpserver/ztpserver.conf and
          check the value of ``identifier``

.. End of Add a Static Node Entry


Create a Pattern (if Topology Validation is enabled)
----------------------------------------------------

Objective
^^^^^^^^^



Solution
^^^^^^^^

Log into your (v)EOS node to get its System ID. If it's in ZTP Mode, just log in
with username ``admin``:

.. code-block:: shell

  switch-name> show version

.. note:: Note down the System ID(System MAC Address or Serial Number).

Let's create a nodes directory for this device:

.. code-block:: shell

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the nodes directory, where all node information is stored
  admin@ztpserver:~# cd nodes

  # Create a directory using the MAC Address you found earlier
  admin@ztpserver:~# mkdir <SYSTEM_ID>


Explanation
^^^^^^^^^^^

A node is considered to be statically provisioned when a directory with its
System ID is already located in the ``nodes/`` directory.

Note that the System ID can be the node's System MAC Address or its Serial Number.

Just adding this directory is not enough to provision the node. The remaining
recipes will finish off the task.  To successfully provision a node
statically, you will need to create:

* ``startup-config``
* ``pattern`` file - if Topology Validation is enabled
* ``definition`` - if you choose to apply other actions during provisioning

and place them in ``[data_root]/nodes/<SYSTEM_ID>``.

.. note:: Confirm your ZTPServer Configuration will identify a node based upon
          the desired System ID by checking /etc/ztpserver/ztpserver.conf and
          check the value of ``identifier``

.. End of Add a Static Node Entry
