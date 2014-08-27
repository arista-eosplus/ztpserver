Configuration
=============

.. contents:: :local:

The ZTPServer uses a series of YAML files to provide its various
configuration and databases. Use of the YAML format makes the file
easier to read and makes it easier and more intuitive to add/update
entries (as opposed to other files formats such as JSON, or binary
formats such as SQL).


Configuration Types
~~~~~~~~~~~~~~~~~~~

There are 2 general types of configurations supported by ZTPServer, `Static <static_provisioning_>`_ and `Dynamic <dynamic_provisioning_>`_ provisioning.

.. _static_provisioning:

Static provisioning:
^^^^^^^^^^^^^^^^^^^^

Manually create node entries in /nodes and a startup-configuration. In order to do that:

* Create a new directory for each node under [data_root]/nodes, using the system unique_id as the name.
* Place a startup-config in the newly-created folder.

Example:

.. code-block:: console

    [root@localhost ztpserver]# mkdir /usr/share/ztpserver/nodes/000c29f3a39g
    [root@localhost ztpserver]# cp myconfig /usr/share/ztpserver/nodes/000c29f3a39g/startup-config

Topology validation is still an active component of a static provisioning configuration at defaults. This allows a customer to validate cabling even with a statically defined node.  If ``disable_topology_validation = true`` in ``/etc/ztpserver/ztpserver.conf`` then you won’t need to create a pattern file in the directory for topology validation, if it is set to “false” (default), then you’ll need to place a “pattern” file in the specific node directory, using a similar syntax as neighbordb. 

e.g.:
``/usr/share/ztpserver/nodes/ABC12345678/pattern``

This can be as simple as below, but must exist. See the :ref:`static_neighbordb_example` example.
::

    name: static_node
    interfaces:
    - any: any:any

.. _dynamic_provisioning:

Dynamic provisioning:
^^^^^^^^^^^^^^^^^^^^^

This method assumes that you do not create a node entry for each node manually. Instead create a neighbordb entry with at least one pattern that maps to a definition. This requires editing: 
/usr/share/ztpserver/neighbordb

And creating at least one pattern. See the :ref:`dynamic_neighbordb_example` example.

Once you’ve created the neighbordb entry, you’ll need to match a definition file placed in:
/usr/share/ztpserver/definitions/

See the :ref:`dynamic_definition_example` example.

The combination of a neighbordb match and a template definition with dynamic resource allocation allow the same definition to be used for multiple nodes. 

Global configuration
~~~~~~~~~~~~~~~~~~~~

.. _global_configuration:

Global configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^

The global ZTPServer configuration file can be found at ``/etc/ztpserver/ztpserver.conf``. It uses INI format. (For format details, see top section `Python configparser <https://docs.python.org/2/library/configparser.html>`_).

An alternate location for the global configuration file may be specified by using the ``--conf`` command line option:
e.g.

::

    (bash)# ztps --help
    usage: ztpserver [options]

    optional arguments:
      -h, --help            show this help message and exit
      --version, -v         Displays the version information
      --conf CONF, -c CONF  Specifies the configuration file to use
      --validate FILENAME   Runs a validation check on neighbordb
      --debug               Enables debug output to the STDOUT
    (bash)# ztps --conf /var/ztps.conf

If the global configuration file is updated, the server must be restarted in order to pick up the new configuration.

Sections and attributes
'''''''''''''''''''''''

.. code-block:: ini

    [default]

    # Location of all ztps boostrap process data files
    # default=/var/lib/ztpserver
    data_root=<PATH>

    # UID used in the /nodes structure (serialnum is not supported yet)
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

    [files]
    # Path for the files directory (overriding data_root/files)
    # default=files
    folder=<path>
    # default=data_root (from above)
    path_prefix=<path>

    [actions]
    # Path for the actions directory (overriding data_root/actions)
    # default=actions
    folder=<path>
    # default=data_root (from above)
    path_prefix=<path>

    [bootstrap]
    # Path for the bootstrap directory (overriding data_root/bootstrap)
    # default=bootstrap
    folder=<path>
    # default=data_root (from above)
    path_prefix=<path>

    # Bootstrap filename
    # default=bootstrap
    filename=<name>

    [neighbordb]
    # Neighbordb filename (file located in data_root)
    # default=neighbordb
    filename=<name>

Environment Variables in the global configuration
'''''''''''''''''''''''''''''''''''''''''''''''''

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

Data Directory Structure
''''''''''''''''''''''''

The ZTPServer side components are housed in a single directory defined by the ``data_root`` variable in the global configuration file. The directory location will vary depending on the configuration in ``/etc/ztpserver/ztperserver.conf``. The data\_root is loaded when ztps is executed. The following directory structure is normally used:

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
                .node
                attributes
        actions/
        files/
        definitions/
        resources/
        neighbordb

Bootstrap configuration
^^^^^^^^^^^^^^^^^^^^^^^

``[data_root]/bootstrap/`` contains files that control the bootstrap process on a node.

-  **bootstrap** is the base bootstrap script which is going to be served to all clients in order to start and run the bootstrap process. Before serving the script to the clients, the server replaces any references to $SERVER with the value of ``server_url`` in the global configuration file

-  **bootstrap.conf** is a configuration file which defines the local logging configuration on the nodes (during the bootstrap process). The file is loaded on each request.

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

Node-specific configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``[data_root]/nodes/`` contains node-specific configuration files.

Startup configuration
^^^^^^^^^^^^^^^^^^^^^

``startup-config`` provides a static startup configuration file. If this file is present in a node’s folder, when the node sends a GET request to ``/nodes/<unique_id>`` where unique_id is either the serial number or system-mac, the server will respond with a static definition that includes:

-  a **replace\_config** action which will install the configuration file on the switch (see `actions <#actions>`__ section below for more on this)
-  all the **actions** from the local **definition** file (see definition section below for more on this) which have the ``always_execute`` attribute set to ``True``

Definition file
^^^^^^^^^^^^^^^

The **definition** file is the collection of actions which are going to be
performed during the bootstrap process for the node. The definition file
can be either: **manually created** OR **auto-generated by the server**
when the node matches one of the patterns in **neighbordb**. The
definition file is generated based on the definition file associated
with the matching pattern in **neighbordb**.

.. code-block:: yaml

    name: <system name>

    actions:
        - name: <name> 
        action: <action name>

        attributes:                     # attributes at action scope
            always_execute: True        # optional, default False
            <key>: <value>
            <key>: <value>

        onstart:   <msg>                # message to log before action is executed
        onsuccess: <msg>                # message to log if action execution succeeds
        onfailure: <msg>                # message to log if action execution fails

    attributes:                         # attributes at global scope
        <key>: <value>
        <key>: <value>
        <key>: <value>

Attributes
''''''''''

Attributes are either key/value pairs, key/dictionary pairs, key/list pairs or key/reference pairs. They are all sent to the client in order to be passed in as arguments to actions.

key/reference pairs are evaluated before being sent to the client.

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
           - my_value1
           - my_value2
           - my_valueN

-  key/reference:

   .. code-block:: yaml

       attributes:
           my_attribute : $my_other_attribute

**key/reference** attributes are identified by the fact that the value starts with the ‘$’ sign, followed by the name of another attribute. They are evaluated before being sent to the client

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

    For release 1.0, only **one level of indirection** is
    allowed - if multiple levels of indirection are used, then the data
    sent to the client will contain unevaluated key/reference pairs in
    the attributes list (which might lead to failures or unexpected
    results in the client).

The values of the attributes can be either strings, lists, dictionaries, references to other attributes or functions.

The supported functions are:

-  **allocate(resource\_pool)** - allocate available resource from
   resource pool; the allocation is perform on the server side and the
   result of the allocation is passed to the client via the definition

.. note::

    Functions can only be used with strings as arguments,
    currently. See section on `add\_config <#actions>`__ action for
    examples.

Attributes can be defined in three places:

    -  in the node’s attributes file (see below)
    -  in the definition, at global scope
    -  in the definition, at action scope

For key/value, key/list and and key/reference attributes, in case of
conflicts between the three scopes, the following order of precidence rules are
applied to determine the final value to send to the client:

    1. action scope in the definition takes precedence
    2. attributes file comes next
    3. global scope in the definition comes last

For key/dict attributes, in case of conflicts between the scopes, the
dictionaries are merged. In the event of dictionary key conflicts, the same
precidence rules from above apply.

Pattern file
^^^^^^^^^^^^

The **pattern** file provides a :ref:`statically typed <static_provisioning>` pattern match which is
used to validate the node's neighbors during the bootstrap process (if
topology validation is enabled). The pattern file can be either:

    -  manually created
    -  auto-generated by the server, when the node matches one of the patterns in ``neighbordb``. The pattern that is matched in ``neighbordb`` is, then, written to this file and used for topology validation in subsequent re-runs of the bootstrap process.

The format of a pattern is very similar to the format of ``neighordb``
(see `neighbordb <#neighbordb>`__ section below):

.. code-block:: yaml

    variables:
        <variable_name>: <function>
    ...

    name: <single line description of pattern>
    definition: <defintion_url>
    interfaces:
        - <port_name>:<system_name>:<neighbor_port_name>:<tags>
        - <port_name>:
            device: <system_name>
            port: <neighbor_port_name>
            tags: <comma delimited tags list>
    ...

If the pattern file is missing when the node makes a GET request for its
definition, the server will log a message and return either:

    -  400 (BAD\_REQUEST) if topology validation is enabled
    -  200 (OK) if topology validation is disabled

If topology validation is enabled, the following pattern can be used in
order to disable it locally for a node (the pattern from below will
match **any** node):

.. code-block:: yaml

    name: <pattern name>
    interfaces:
        - any: any:any   

Node details
^^^^^^^^^^^^

The ``.node`` file contains a cached copy of the node’s details that were
received during the POST request the node makes to ``/nodes (URI)``.
This cache is used to validate the node’s neighbors against the
``pattern`` file, if topology validation is enabled (during the GET
request the node makes in order to retrieve its definition).

Attributes file
^^^^^^^^^^^^^^^

``attributes`` is a file which can be used in order to store attributes
associated with the node’s definition. This is especially useful
whenever multiple nodes share the same definition - in that case,
instead of having to edit each node’s definition in order to add the
attributes (at the global or action scope), all nodes can share the same
definition (which might be symlinked to their individual node folder)
and the user only has to create the attributes file for each node. The
``attributes`` file should be a valid key/value YAML file.

Actions
~~~~~~~

``[data_root]/actions/`` contains all of the actions available for use in
definitions. More details about each action can be found at the top of
the corresponding Python file.

+---------------------------+-----------------------------------------------------------+----------------------------------------+
| Action                    | Description                                               | Required Attributes                    |
+===========================+===========================================================+========================================+
| :mod:`add_config` *       | Adds a section of config to the final startup-config file | url                                    |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`copy_file`          | Copies a file from the server to the destination node     | src\_url, dst\_url, overwrite, mode    |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_cli_plugin` | Installs a new EOS CLI plugin and configures rc.eos       | url                                    |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_extension`  | Installs a new EOS extension                              | extension\_url, autoload, force        |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`install_image`      | Validates and installs a specific version of EOS          | url, version                           |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`replace_config`     | Sends an entire startup-config to the node (overrides     | url                                    |
|                           | (overrides add\_config)                                   |                                        |
+---------------------------+-----------------------------------------------------------+----------------------------------------+
| :mod:`send_email`         | Sends an email to a set of recipients routed              | smarthost, sender, receivers, subject, |
|                           | through a relay host. Can include file attachments        | body, attachments, commands            |
+---------------------------+-----------------------------------------------------------+----------------------------------------+

Additional details on each action are available in the :doc:`actions` module docs.

.. note::

    * The 'add_config' action supports applying block of EOS configuration commands to a node’s startup-config.

e.g.

Let’s assume that we have a block of configuration that adds a list of
NTP servers to the startup configuration. The action would be
constructed as such:

.. code-block:: yaml

    actions:
        - name: configure NTP
          action: add_config
          attributes:
            url: /files/templates/ntp.template

The above action would reference the ``ntp.template`` file which would
configure NTP. The template file could look like the one from below:

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

e.g. Let’s assume a need for a more generalized template that only needs
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

Resources
~~~~~~~~~

``[data_root]/files/`` contains the files that actions might request
from the server. For example, ``[data_root]/files/images/`` could contain
all EOS SWI files.

Definitions
~~~~~~~~~~~

``[data_root]/definitions/`` contains a set of shared definition files
which can be associated with pattern in neighbordb (see the :ref:`neighbordb`
section below) or symlink-ed from nodes’ folders.

Resource pools
~~~~~~~~~~~~~~

``[data_root]/resources/`` contains global resource pools from which
attributes in definitions can be allocated via the allocate(...)
function.

The resource pools provide a way to dynamically allocate a resource to a
node when the node definition is created. The resource pools are
key/value YAML files that contain a set of resources to be allocated to
a node (whenever the allocate(...) function is used in the definition).

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

.. _neighbordb:

Neighbordb
~~~~~~~~~~

The ``neighbordb`` YAML file defines mappings between node descriptions
and node definitions. If a node does not already have a node
definition, then the node’s details are attempted to be matched against
the patterns in ``neighbordb``. If a match is successful, then a node
definition will be automatically generated for the node.

.. code-block:: yaml

    variables:
        variable_name: function
    ...
    patterns*:
        - name*: <single line description of pattern>
          definition*: <defintion_url>
          node: <unique_id>
          variables:
            <variable_name>: <function>
          interfaces*:
            - <port_name>*: <system_name>*:<neighbor_port_name>:<tags>
            - <port_name>*:
                device*: <system_name>*
                port: <neighbor_port_name>
                tags: <comma delimited tags list>
    ...

.. note::

    Itemsmarked wiht \* are mandatory elements. Everything else is optional.

variables
^^^^^^^^^

This section allows for the definition of variables in neighbordb. The
variables can be used to match remote device and/or interface names
(``<system_name>``, ``<neighbor_port_name>`` above) of a node during
the pattern matching stage. The supported values are:

string
    same as exact(string) from below

exact (pattern)
    defines a pattern that must be matched exactly (Note: this is the default function if another function is not specified)
regex (pattern)
    defines a regex pattern to match the node name against
includes (string)
    defines a string that must be present in the node name
excludes (string)
    defines a string that must not be present in the node name

itentifier
''''''''''

System serial number or MAC address of a node, depending on the global 'identifier' setting in ztpserver.conf.

port\_name
''''''''''

Local node interface - supported values (MUST start with **“Ethernet”**,
if not keyword):

-  **Any interface**

   -  any

-  **No interface**

   -  none

-  **Explicit interface**

   -  Ethernet1
   -  Ethernet2/4

-  **Interface list/range**

   -  Ethernet1-2
   -  Ethernet1,3
   -  Ethernet1-2,3/4
   -  Ethernet1-2,4
   -  Ethernet1-2,4,6
   -  Ethernet1-2,4,6,8-9
   -  Ethernet4,6,8-9
   -  Ethernet10-20
   -  Ethernet1/3-2/4 *
   -  Ethernet3-$ *
   -  Ethernet1/10-$ *

-  **All Interfaces on a Module**

   -  Ethernet1/$ *

.. note::

    \* Available in future releases.

system\_name:neighbor\_port\_name
'''''''''''''''''''''''''''''''''

Remote system and interfaces - supported values (STRING = any string
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
                    

1. ``any: any:any``: matches anything
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

tags
''''

Supported in future releases.
