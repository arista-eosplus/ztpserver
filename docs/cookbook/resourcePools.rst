Resource Pools
==============

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Add a New Resource Pool
-----------------------

Objective
^^^^^^^^^

I'd like to add a new resource pool of IP addresses so that I can assign a new
IP to each node that gets provisioned.

.. note:: Resource Pools are simple ``key: value`` YAML files.


Solution
^^^^^^^^

**Create the resource pool**

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Create a resource pool file
  admin@ztpserver:~# vi resources/mgmt_ip

.. code-block:: yaml

  192.168.0.2/24: null
  192.168.0.3/24: null
  192.168.0.4/24: null
  192.168.0.5/24: null
  192.168.0.6/24: null
  192.168.0.7/24: null
  192.168.0.8/24: null
  192.168.0.9/24: null
  192.168.0.10/24: null


Explanation
^^^^^^^^^^^

Resource Pool files are just ``key: value`` files. The default value for each
key should be ``null``.  This makes the key available for assignment. If you would
like to pre-assign a specific node with a particular key, then just put the
node's node_id in place of ``null``.  Resource Pools are analyzed when the
``allocate(pool_name)`` function is run from a definition.  Note that you can
also use the ``allocate()`` function to perform a lookup when a node has
already been assigned a key.


.. End of Add a New Resource Pool


Clearing a Resource Pool
------------------------

Objective
^^^^^^^^^

I'd like to reset the values of a resource pool so that all values return to
``null``.


Solution
^^^^^^^^

You can use the ztps command line to perform this action.

.. code-block:: console

  admin@ztpserver:~# ztps --clear-resources

.. note:: This will clear **ALL** resource pools


Explanation
^^^^^^^^^^^

Clearing all resource pools can be done via the command line on the ZTPServer.
The command will analyze ``data_root/resources`` and any file that exists in
that directory that resembles a ZTPServer resource pool will be cleared. 

.. End of Clearing a Resource Pool
