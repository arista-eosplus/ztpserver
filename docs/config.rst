Configuration
=============

.. contents:: :local:

Overview
~~~~~~~~

The ZTPServer uses a series of YAML files to provide its various
configuration and databases. Use of the YAML format makes the files
easier to read and makes it easier and more intuitive to add/update
entries (as opposed to other files formats such as JSON, or binary
formats such as SQL).


The ZTPServer components are housed in a single directory defined by the ``data_root`` variable in the global configuration file. The directory location will vary depending on the configuration in ``/etc/ztpserver/ztperserver.conf``.

The following directory structure is normally used:

.. code-block:: ini

    [data_root]
        bootstrap/
            bootstrap
            bootstrap.conf
        nodes/
            <unique_id)>/
                startup-config
                definition
                pattern
                config-handler
                .node
                attributes
        actions/
        files/
        definitions/
        resources/
        neighbordb


All configuration files can be validated using:

::

    (bash)# ztps --validate

.. _global_configuration:

Global configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~

The global ZTPServer configuration file can be found at ``/etc/ztpserver/ztpserver.conf``. It uses the INI format (for details, see top section of `Python configparser <https://docs.python.org/2/library/configparser.html>`_).

An alternative location for the global configuration file may be specified by using the ``--conf`` command line option:

e.g.

::

    (bash)# ztps --help
    usage: ztpserver [options]

    optional arguments:
      -h, --help            show this help message and exit
      --version, -v         Displays the version information
      **--conf CONF, -c CONF  Specifies the configuration file to use**
      --validate-config, -V
                            Validates config files
      --debug               Enables debug output to the STDOUT
      --clear-resources, -r
                            Clears all resource files
    (bash)# ztps --conf /var/ztps.conf

If the global configuration file is updated, the server must be restarted in order to pick up the new configuration.

.. code-block:: ini

    [default]

    # Location of all ztps boostrap process data files
    # default= /usr/share/ztpserver
    data_root=<PATH>

    # UID used in the /nodes structure
    # default=serialnum
    identifier=<serialnum | systemmac>

    # Server URL to-be-advertised to clients (via POST replies) during the bootstrap process
    # default=http://ztpserver:8080
    server_url=<URL>

    # Enable local logging
    # default=True
    logging=<True | False>

    # Enable console logging
    # default=True
    console_logging=<True | False>

    # Console logging format
    # default=%(asctime)-15s:%(levelname)s:[%(module)s:%(lineno)d] %(message)s
    console_logging_format=<(Python)logging format>

    # Globally disable topology validation in the bootstrap process
    # default=False
    disable_topology_validation=<True | False>

    [server]
    # Note: this section only applies to using the standalone server.  If
    # running under a WSGI server, these values are ignored

    # Interface to which the server will bind to (0:0:0:0 will bind to
    # all available IPv4 addresses on the local machine)
    # default=0.0.0.0
    interface=<IP addr>

    # TCP listening port
    # default=8080
    port=<TCP port>

    [bootstrap]
    # Bootstrap filename (file located in <data_root>/bootstrap)
    # default=bootstrap
    filename=<name>

    [neighbordb]
    # Neighbordb filename (file located in <data_root>)
    # default=neighbordb
    filename=<name>

.. note::

    Configuration values may be overridden by setting environment variables, if the configuration attribute supports it. This is mainly used for testing and should not be used in production deployments.

Configuration values that support environment overrides use the ``environ`` keyword, as shown below:

.. code-block:: python

    runtime.add_attribute(StrAttr(
        name='data_root',
        default='/usr/share/ztpserver',
        environ='ZTPS_DEFAULT_DATAROOT'
    ))

In the above example, the ``data_root`` value is normally configured in the [default] section as ``data_root``; however, if the environment variable ``ZTPS_DEFAULT_DATAROOT`` is defined, it will take precedence.

.. _bootstrap_config:

Bootstrap configuration
~~~~~~~~~~~~~~~~~~~~~~~~

``[data_root]/bootstrap/`` contains files that control the bootstrap process of a node.

-  **bootstrap** is the base bootstrap script which is going to be served to all clients in order to control the bootstrap process. Before serving the script to the clients, the server replaces any references to $SERVER with the value of ``server_url`` in the global configuration file.

-  **bootstrap.conf** is a configuration file which defines the local logging configuration on the nodes (during the bootstrap process). The file is loaded on on-demand.

   e.g.

   .. code-block:: yaml

      ---
      logging:
        -
          destination: "ztps.ztps-test.com:514"
          level: DEBUG
        - destination: file:/tmp/ztps-log
          level: DEBUG
        - destination: ztps-server:1234
          level: CRITICAL
        - destination: 10.0.1.1:9000
          level: CRITICAL
      xmpp:
        domain: im.ztps-test.com
        username: bootstrap
        password: eosplus
        rooms:
          - ztps
          - ztps-room2

.. note::

    In order for XMPP logging to work, a non-EOS user need to be connected to the room specified in bootstrap.conf, before the ZTP process starts. The room has to be created (by the non-EOS user) before the bootstrap client starts logging the ZTP process via XMPP.


.. _static_provisioning:

Static provisioning - overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A node can be statically configured on the server as follows:

* create a new directory under ``[data_root]/nodes``, using the system's unique_id as the name
* create/symlink a *startup-config* or *definition* file in the newly-created folder
* if topology validation is enabled, also create/symlink a *pattern* file
* optionally, create *config-handler* script which is run whenever a PUT startup-config request succeeds

Static provisioning - startup_config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``startup-config`` provides a static startup-configuration for the node. If this file is present in a node’s folder, when the node sends a GET request to ``/nodes/<unique_id>``, the server will respond with a static definition that includes:

-  a **replace\_config** action which will install the configuration file on the switch (see `actions <#actions>`__ section below for more on this). This action will be placed **first** in the definition.
-  all the **actions** from the local **definition** file (see definition section below for more on this) which have the ``always_execute`` attribute set to ``True``


.. _definition:

Static provisioning - definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **definition** file contains the set of actions which are going to be
performed during the bootstrap process for a node. The definition file
can be either: **manually created** OR **auto-generated by the server**
when the node matches one of the patterns in **neighbordb** (in this case the
definition file is generated based on the definition file associated
with the matching pattern in **neighbordb**).

.. code-block:: yaml

    name: <system name>

    actions:
      -
        action: <action name>

        attributes:                     # attributes at action scope
            always_execute: True        # optional, default False
            <key>: <value>
            <key>: <value>

        onstart:   <msg>                # message to log before action is executed
        onsuccess: <msg>                # message to log if action execution succeeds
        onfailure: <msg>                # message to log if action execution fails
      ...

    attributes:                         # attributes at global scope
        <key>: <value>
        <key>: <value>
        <key>: <value>

Static provisioning - attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Attributes are either key/value pairs, key/dictionary pairs, key/list pairs or key/reference pairs. They are all sent to the client in order to be passed in as arguments to actions.

Here are a few examples:

-  key/value:

   .. code-block:: yaml

       attributes:
           my_attribute : my_value

-  key/dictionary

   .. code-block:: yaml

       attributes:
           my_dict_attribute:
               key1: value1
               key2: value2

-  key/list:

   .. code-block:: yaml

       attributes:
         list_name:
           - my_value1
           - my_value2
           - my_valueN

-  key/reference:

   .. code-block:: yaml

       attributes:
           my_attribute : $my_other_attribute

**key/reference** attributes are identified by the fact that the value starts with the ‘$’ sign, followed by the name of another attribute. They are evaluated before being sent to the client.

   Example:

   .. code-block:: yaml

       attributes:
           my_other_attribute: dummy
           my_attribute : $my_other_attribute

   will be evaluated to:

   .. code-block:: yaml

       attributes:
           my_other_attribute: dummy
           my_attribute : dummy

If a reference points to a non-existing attribute, then the variable
substitution will result in a value of *None*.

.. note::

    Only **one level of indirection** is
    allowed - if multiple levels of indirection are used, then the data
    sent to the client will contain unevaluated key/reference pairs in
    the attributes list (which might lead to failures or unexpected
    results in the client).

The values of the attributes can be either strings, numbers, lists, dictionaries, or references to other attributes or plugin references for allocating resources.

Plugins can be used to allocate resources on the server side and then pass the result of the allocation back to the client via the definition. The supported plugins are:

-  **allocate(resource\_pool)** - allocates an available resource from a file-based resource pool
-  **sqlite(resource\_pool)** - allocates an available resource from a sqlite database


.. note::

    Plugins can only be referenced with strings as arguments,
    currently. See section on `add\_config <#actions>`__ action for
    examples.

Attributes can be defined in three places:

    -  in the definition, at action scope
    -  in the definition, at global scope
    -  in the node’s attributes file (see below)

``attributes`` is a file which can be used in order to store attributes
associated with the node’s definition. This is especially useful
whenever multiple nodes share the same definition - in that case,
instead of having to edit each node’s definition in order to add the
attributes (at the global or action scope), all nodes can share the same
definition (which might be symlinked to their individual node folder)
and the user only has to create the attributes file for each node. The
``attributes`` file should be a valid key/value YAML file.

.. code-block:: yaml

    <key>: <value>
    <key>: <value>
    ...

For key/value, key/list and and key/reference attributes, in case of
conflicts between the three scopes, the following order of precidence rules are
applied to determine the final value to send to the client:

    1. action scope in the definition takes precedence
    2. attributes file comes next
    3. global scope in the definition comes last

For key/dict attributes, in case of conflicts between the scopes, the
dictionaries are merged. In the event of dictionary key conflicts, the same
precidence rules from above apply.

Static provisioning - pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``pattern`` file a way to validate the node's topology during the bootstrap process (if topology validation is enabled). The pattern file can be either:

    -  manually created
    -  auto-generated by the server, when the node matches one of the patterns in ``neighbordb`` (the pattern that is matched in ``neighbordb`` is, then, written to this file and used for topology validation in subsequent re-runs of the bootstrap process)

The format of a pattern is very similar to the format of ``neighordb``
(see `neighbordb <#neighbordb>`__ section below):

.. code-block:: yaml

    variables:
        <variable_name>: <function>
    ...

    name: <single line description of pattern>               # optional
    interfaces:
        - <port_name>:<system_name>:<neighbor_port_name>
        - <port_name>:
            device: <system_name>
            port: <neighbor_port_name>
    ...

If the pattern file is missing when the node makes a GET request for its definition, the server will log a message and return either:

    -  400 (BAD\_REQUEST) if topology validation is enabled
    -  200 (OK) if topology validation is disabled

If topology validation is enabled globally, the following patterns can be used in order to disable it for a particular node:

    -  match **any** node which has at least one LLDP-capable neighbor:

.. code-block:: yaml

    name: <pattern name>
    interfaces:
        - any: any:any

OR

    -  match **any** node which has no LLDP-capable neighbors:

.. code-block:: yaml

    name: <pattern name>
    interfaces:
        - none: none:none

Static provisioning - config-handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``config-handler`` file can be any script which can be executed
on the server. The script will be executed every time a PUT startup-config
request succeeds for the node.

The script can be used for raising alarms, performing checks, submitting
the startup-config file to a revision control system, etc.

Static provisioning - log
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.node`` file contains a cached copy of the node’s details that were
received during the POST request the node makes to ``/nodes (URI)``.
This cache is used to validate the node’s neighbors against the
``pattern`` file, if topology validation is enabled (during the GET
request the node makes in order to retrieve its definition).

The ``.node`` is created automatically by the server and should not be edited manually.

Example .node file:

.. code-block:: json

    {"neighbors": {"Management1": [{"device": "mgmt-server",
                                    "port": "0050.569b.ad8d"},
                                   {"device": "veos-leaf3.ztps-test.com",
                                    "port": "Management1"},
                                   {"device": "veos-spine2.ztps-test.com",
                                    "port": "Management1"}
                                   ],
                   "Ethernet1": [{"device": "veos-leaf3.ztps-test.com",
                                  "port": "Ethernet1"}
                                ],
                   "Ethernet3": [{"device": "veos-spine2.ztps-test.com",
                                  "port": "Ethernet3"}
                                ]
                  },
     "model": "vEOS",
     "version": "4.15.1F",
     "systemmac": "005056600663"
    }

.. _dynamic_provisioning:

Dynamic provisioning - overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A node can be dynamically provisioned by creating a matching ``neighbordb`` (``[data_root]/neighbordb``) entry which maps to a definition. The entry can potentially match multiple nodes.
The associated definition should be created in [data_root]/definitions/.

.. _neighbordb:

Dynamic provisioning - neighbordb
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``neighbordb`` YAML file defines mappings between patterns
and definitions. If a node is not already configured via a static entry,
then the node’s topology details are attempted to be matched against
the patterns in ``neighbordb``. If a match is successful, then a node
definition will be automatically generated for the node (based on the
mapping in neighbordb).

There are 2 types of patterns supported in neighbordb:
node-specific (containing the **node** attribute, which refers to the
unique_id of the node) and global patterns.

Rules:

 - if multiple node-specific entries reference the same unique_id, only the first will be in effect - all others will be ignored
 - if both the **node** and **interfaces** attributes are specified and a node's unique_id is a match, but the topology information is not, then the overall match will fail and the global patterns will not be considered
 - if there is no matching node-specific pattern for a node's unique_id, then the server will attempt to match the node against the global patterns (in the order they are specified in ``neighbordb``)
 - if a node-specific pattern matches, the server will automatically generate an open pattern in the node's folder. This pattern will match any device with at least one LLDP-capable neighbor.  Example: ``any: any:any``

.. code-block:: yaml

    ---
    variables:
        variable_name: function
    ...
    patterns:
        - name: <single line description of pattern>
          definition: <defintion_url>
          node: <unique_id>
          config-handler: <config-handler>
          variables:
            <variable_name>: <function>
          interfaces:
            - <port_name>: <system_name>:<neighbor_port_name>
            - <port_name>:
                device: <system_name>
                port: <neighbor_port_name>
    ...

.. note::

    Mandatory attributes: **name**, **definition**, and either **node**, **interfaces** or both.

    Optional attributes: **variables**, **config-handler**.

variables
'''''''''

The variables can be used to match the remote device and/or port name (``<system_name>``, ``<neighbor_port_name>`` above) for a neighbor. The supported values are:

**string**
    same as exact(string) from below

exact (pattern)
    defines a pattern that must be matched exactly (Note: this is the default function if another function is not specified)
regex (pattern)
    defines a regex pattern to match the node name against
includes (string)
    defines a string that must be present in system/port name
excludes (string)
    defines a string that must not be present in system/port name

node: unique_id
'''''''''''''''

Serial number or MAC address, depending on the global 'identifier' attribute in **ztpserver.conf**.

interfaces: port\_name
''''''''''''''''''''''

Local interface name - supported values:

-  **Any interface**

   -  any

-  **No interface**

   -  none

-  **Explicit interface**

   -  Ethernet1
   -  Ethernet2/4
   -  Management1

-  **Interface list/range**

   -  Ethernet1-2
   -  Ethernet1,3
   -  Ethernet1-2,3/4
   -  Ethernet1-2,4
   -  Ethernet1-2,4,6
   -  Ethernet1-2,4,6,8-9
   -  Ethernet4,6,8-9
   -  Ethernet10-20
   -  Ethernet1/3-1/32

system\_name:neighbor\_port\_name
'''''''''''''''''''''''''''''''''

Remote system and interface name - supported values (STRING = any string
which does not contain any white spaces):

-  ``any``: interface is connected
-  ``none``: interface is NOT connected
-  ``<STRING>:<STRING>``: interface is connected to specific
   device/interface
-  ``<STRING>`` (Note: if only the device is configured, then ‘any’ is
   implied for the interface. This is equal to ``<DEVICE>:any``):
   interface is connected to device
-  ``<DEVICE>:any``: interface is connected to device
-  ``<DEVICE>:none``: interface is NOT connected to device (might be
   connected or not to some other device)
-  ``$<VARIABLE>:<STRING>``: interface is connected to specific
   device/interface
-  ``<STRING>:<$VARIABLE>``: interface is connected to specific
   device/interface
-  ``$<VARIABLE>:<$VARIABLE>``: interface is connected to specific
   device/interface
-  ``$<VARIABLE>`` (‘any’ is implied for the interface. This is equal to
   ``$<VARIABLE>:any``): interface is connected to device
-  ``$<VARIABLE>:any``: interface is connected to device
-  ``$<VARIABLE>:none``: interface is NOT connected to device (might be
   connected or not to some other device)

port\_name: system\_name:neighbor\_port\_name
'''''''''''''''''''''''''''''''''''''''''''''

Negative constraints


1.  ``any: DEVICE:none``: no port is connected to DEVICE
2.  ``none: DEVICE:any``: same as above
3.  ``none: DEVICE:none``: same as above
4.  ``none: any:PORT``: no device is connected to PORT on any device
5.  ``none: DEVICE:PORT``: no device is connected to DEVICE:PORT
6.  ``INTERFACES: any:none``: interfaces not connected
7.  ``INTERFACES: none:any``: same as above
8.  ``INTERFACES: none:none``: same as above
9.  ``INTERFACES: none:PORT``: interfaces not connected to PORT on any
    device
10. ``INTERFACES: DEVICE:none``: interfaces not connected to DEVICE
11. ``any: any:none``: bogus, will prevent pattern from matching
    anything
12. ``any: none:none``: bogus, will prevent pattern from matching
    anything
13. ``any: none:any``: bogus, will prevent pattern from matching
    anything
14. ``any: none:PORT``: bogus, will prevent pattern from matching
    anything
15. ``none: any:any``: bogus, will prevent pattern from matching
    anything
16. ``none: any:none``: bogus, will prevent pattern from matching
    anything
17. ``none: none:any``: bogus, will prevent pattern from matching
    anything
18. ``none: none:none``: bogus, will prevent pattern from matching
    anything
19. ``none: none:PORT``: bogus, will prevent pattern from matching
    anything

Positive constraints


1. ``any: any:any``: "Open pattern" matches anything
2. ``any: any:PORT``: matches any interface connected to any device’s
   PORT
3. ``any: DEVICE:any``: matches any interface connected to DEVICE
4. ``any: DEVICE:PORT``: matches any interface connected to DEVICE:PORT
5. ``INTERFACES: any:any``: matches if local interfaces is one of
   INTERFACES
6. ``INTERFACES: any:PORT``: matches if one of INTERFACES is connected
   to any device’s PORT
7. ``INTERFACES: DEVICE:any``: matches if one of INTERFACES is connected
   to DEVICE
8. ``INTERFACES: DEVICE:PORT``: matches if one of INTERFACES is
   connected to DEVICE:PORT

Definitions
~~~~~~~~~~~

``[data_root]/definitions/`` contains a set of shared definition files
which can be associated with patterns in ``neighbordb`` (see the :ref:`neighbordb`
section below) or added to/symlink-ed from nodes’ folders.

See :ref:`definition` for more.

Actions
~~~~~~~

``[data_root]/actions/`` contains the set of all actions available for use in
definitions.

New custom actions to-be referenced from definitions can be added to
``[data_root]/actions/``. These will be loaded on-demand and do not require
a restart of the ZTPServer. See ``[data_root]/actions`` for examples.

+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| Action                          | Description                                               | Required Attributes                    |
+=================================+===========================================================+========================================+
| :mod:`add_config`               | Adds a block of configuration to the final startup-config | url                                    |
|                                 | file                                                      |                                        |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`configure_ansible_client` | Create user and configure keys for Ansible deployment     | user, passwd, group, root, key         |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`copy_file`                | Copies a file from the server to the destination node     | src\_url, dst\_url, overwrite, mode    |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_cli_plugin`       | Installs a new EOS CLI plugin and configures rc.eos       | url                                    |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_extension`        | Installs a new EOS extension                              | extension\_url, autoload, force        |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_image`            | Validates and installs a specific version of EOS          | url, version, downgrade                |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`replace_config`           | Sends an entire startup-config to the node (overrides     | url                                    |
|                                 | (overrides add\_config)                                   |                                        |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`run_bash_script`          | Run bash script during bootstrap.                         | url                                    |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`run_cli_commands`         | Run CLI commands during bootstrap.                        | url                                    |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`send_email`               | Sends an email to a set of recipients routed              | smarthost, sender, receivers, subject, |
|                                 | through a relay host. Can include file attachments        | body, attachments, commands            |
+---------------------------------+-----------------------------------------------------------+----------------------------------------+

Additional details on each action are available in the :doc:`actions` module docs.

e.g.

Assume that we have a block of configuration that adds a list of
NTP servers to the startup configuration. The action would be
constructed as such:

.. code-block:: yaml

    actions:
        - name: configure NTP
          action: add_config
          attributes:
            url: /files/templates/ntp.template

The above action would reference the ``ntp.template`` file which would contain configuration commands to
configure NTP. The template file could look like the following:

.. code-block:: console

    ntp server 0.north-america.pool.ntp.org
    ntp server 1.north-america.pool.ntp.org
    ntp server 2.north-america.pool.ntp.org
    ntp server 3.north-america.pool.ntp.org

When this action is called, the configuration snippet above will be
appended to the ``startup-config`` file.

The configuration templates can also contains **variables**, which are
automatically substituted during the action’s execution. A variable is
marked in the template via the '$' symbol.

e.g.
Let’s assume a need for a more generalized template that only needs
node specific values changed (such as a hostname and management IP
address). In this case, we’ll build an action that allows for **variable
substitution** as follows.

.. code-block:: yaml

    actions:
        - name: configure system
          action: add_config
          attributes:
            url: /files/templates/system.template
            variables:
                hostname: veos01
                ipaddress: 192.168.1.16/24

The corresponding template file ``system.template`` will provide the
configuration block:

.. code-block:: yaml

    hostname $hostname
    !
    interface Management1
        description OOB interface
        ip address $ipaddress
        no shutdown

This will result in the following configuration being added to the
``startup-config``:

.. code-block:: console

    hostname veos01
    !
    interface Management1
        description OOB interface
        ip address 192.168.1.16/24
        no shutdown

Note that in each of the examples, above, the template files are
just standard EOS configuration blocks.

Plugins for allocating resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugins for allocating resources from resource pools
are located in ``[data_root]/plugins/`` and are referenced
by ``<filename>(<resource_pool>)``.

Each plugin contains a ``main`` function with the following signature:

    def main(node_id, pool):
        ...

where:
 - ``node_id`` is the unique_id of the node being provisioned
 - ``pool`` is the name of the resource pool from which an attribute is being allocated

New custom plugins to-be referenced from definitions can be added to
``[data_root]/plugins/``. These will be loaded on-demand and do not require
a restart of the ZTPServer. See ``[data_root]/plugins/test`` for a very basic
example.

**allocate(resource_pool)**

``[data_root]/resources/`` contains global resource pools from which
attributes in definitions can be allocated.

The resource pools provide a way to dynamically allocate a resource to a
node when the node definition is created. The resource pools are
key/value YAML files that contain a set of resources to be allocated to
a node.

.. code-block:: console

    <value1>: <"null"|node_identifier>
    <value2>: <"null"|node_identifier>

In the example below, a resource pool contains a series of 8 IP
addresses to be allocated. Entries which are not yet allocated to a node
are marked using the ``null`` descriptor.

.. code-block:: console

    192.168.1.1/24: null
    192.168.1.2/24: null
    192.168.1.3/24: null
    192.168.1.4/24: null
    192.168.1.5/24: null
    192.168.1.6/24: null
    192.168.1.7/24: null
    192.168.1.8/24: null

When a resource is allocated to a node’s definition, the first available
null value will be replaced by the node’s unique_id. Here is an
example:

.. code-block:: console

    192.168.1.1/24: 001c731a2b3c
    192.168.1.2/24: null
    192.168.1.3/24: null
    192.168.1.4/24: null
    192.168.1.5/24: null
    192.168.1.6/24: null
    192.168.1.7/24: null
    192.168.1.8/24: null

On subsequent attempts to allocate the resource to the same node, ZTPS
will first check to see whether the node has already been allocated a
resource from the pool. If it has, it will reuse the resource instead of
allocating a new one.

In order to free a resource from a pool, simply turn the value
associated to it back to ``null``, by editing the resource file.

Alternatively, ``$ztps --clear-resources`` can be used in order to free
all resources in all file-based resource files.

**sqlite(resource_pool)**

Allocates a resource from a pre-filled sqlite database. The database
is defined by the global variable, 'DB_URL' within the plugin. The database
can include multiple tables, but the value passed into the
'sqlite(resource_pool)' function will be used to look for an available resource.

Table structure should be as follows with the exact column names:

=============== ========
    node_id       key
=============== ========
  NULL           1.1.1.1
  NULL           1.1.1.2
  NULL           1.1.1.3
=============== ========


Which can be created with statements like:

.. code-block:: mysql

  CREATE TABLE `mgmt_subnet`(key TEXT, node_id TEXT)

and add entries with:

.. code-block:: mysql

  INSERT INTO `mgmt_subnet` VALUES('1.1.1.1', NULL)

When a resource is added, the node_id row will be updated
to include the System ID from the switch.

=============== ========
    node_id       key
=============== ========
  001122334455   1.1.1.1
  NULL           1.1.1.2
  NULL           1.1.1.3
=============== ========

On subsequent attempts to allocate the resource to the same node,
ztpserver will first check to see whether the node has already been
allocated a resource from the pool. If it has, it will reuse the
resource instead of allocating a new one.

Definition example:

.. code-block:: yaml

    actions:
      -
        action: add_config
        attributes:
          url: files/templates/ma1.templates
          variables:
            ipaddress: sqlite('mgmt_subnet')
        name: "configure ma1"

.. tip::
  Check out `create_db.py <https://raw.githubusercontent.com/arista-eosplus/ztpserver/develop/utils/create_db.py>`_ for an example script to create a sqlite database.

Config-handlers
~~~~~~~~~~~~~~~

``[data_root]/config-handlers/`` contains config-handlers which can be
associated with nodes via *neighbordb*. A config-handler script is executed
every time a PUT startup-config request succeeds for a node which is
associated to it.

Other files
~~~~~~~~~~~

``[data_root]/files/`` contains the files that actions might request
from the server. For example, ``[data_root]/files/images/`` could contain
all EOS SWI files.
