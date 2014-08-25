.. _install_config:

Initial Configuration
=====================

.. contents:: :local:

There are 2 general types of configurations supported by ZTPServer, `Static <static_provisioning>`_ and `Dynamic <#dynamic_provisioning>`_ provisioning.  For detailed configuration, see the :doc:`config`.

.. _static_provisioning:

Static provisioning:
````````````````````

Manually create node entries in /nodes and a startup-configuration. In order to do that:

* Create a new directory for each node under [data_root]/nodes, using the system unique_id as the name.
* Place a startup-config in the newly-created folder.

Example:

.. code-block:: console

    [root@localhost ztpserver]# mkdir /usr/share/ztpserver/nodes/000c29f3a39g
    [root@localhost ztpserver]# cp myconfig /usr/share/ztpserver/nodes/000c29f3a39g/startup-config

Topology validation is still an active component of a static provisioning configuration at defaults. This allows a customer to validate cabling even with a statically defined node.  If ``disable_topology_validation = true`` in ``/etc/ztpserver/ztpserver.conf`` then you won’t need to create a pattern file in the directory for topology validation, if it is set to “false” (default), then you’ll need to place a “pattern” file in the specific node directory, using a similar syntax as neighbordb. 

e.g.:
``/usr/share/ztpserver/nodes/000c29f3a39g/pattern``

This can be as simple as an ``any: any:any`` statement but must exist. See the :ref:`static_neighbordb_example` example.

.. _dynamic_provisioning:

Dynamic provisioning:
`````````````````````

This method assumes that you do not create a node entry for each node manually. Instead create a neighbordb entry with at least one pattern that maps to a definition. This requires editing: 
/usr/share/ztpserver/neighbordb

And creating at least one pattern. See the :ref:`dynamic_neighbordb_example` example.

Once you’ve created the neighbordb entry, you’ll need to match a definition file placed in:
/usr/share/ztpserver/definitions/

See the :ref:`dynamic_definition_example` example.

The combination of a neighbordb match and a template definition with dynamic resource allocation allow the same definition to be used for multiple nodes. 

