.. raw:: html

   <!-- This is the source for https://github.com/arista-eosplus/ztpserver/wiki/ZTPServer-Reference -->
   <!-- Comments in this document will not be posted externally -->
   <!-- START doctoc generated TOC please keep comment here to allow auto update -->
   <!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

.. raw:: html

   <!-- END doctoc generated TOC please keep comment here to allow auto update -->

ZTPServer Configuration Guide
=============================

.. contents:: Topics

Introduction
------------

ZTPServer provides a robust server which enables comprehensive bootstrap
solutions for Arista EOS network elements.

Prerequisites
~~~~~~~~~~~~~

Server side
^^^^^^^^^^^

-  Python 2.7 or later (https://www.python.org/download/releases)
-  routes 2.0 or later (https://pypi.python.org/pypi/Routes)
-  webob 1.3 or later (http://webob.org/)
-  PyYaml 3.0 or later (http://pyyaml.org/)

Client side
^^^^^^^^^^^

-  EOS 4.12.3 or later

Basic terminology
~~~~~~~~~~~~~~~~~

node
    a node is a EOS instance which is provisioned via ZTPServer. A node is uniquely identified by its system MAC address and/or unique position in the network.

action
    an action is a Python script which is executed during the bootstrap process.

attribute
    an attribute is a variable that holds a value. attributes are used in order to customise the behaviour of actions which are executed during the bootstrap process.

definition
    a definition is a YAML file that contains a collection of all actions (and associated attributes) which need to run during the bootstrap process in order to fully provision a node

pattern
    a pattern is a YAML file which describes a node in terms of its identity (system MAC) and/or location in the network (neighbors)

neighbordb
    neighbordb is a YAML file which contains a collection of patterns which can be used in order to map nodes to definitions

resource pool
    a resource pool is a YAML file which provides a mapping between a set or resources and the nodes to which some of the resources might have been allocated to. The nodes are uniquely identified via their system MAC.

Configuration
-------------

The ZTPServer uses a series of YAML files to provide its various
configuration and databases. Use of the YAML format makes the file
easier to read and makes it easier and more intuitive to add/update
entries (as opposed to other files formats such as JSON, or binary
formats such as SQL).

Global configuration
~~~~~~~~~~~~~~~~~~~~

Global configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^

The global ZTPServer configuration file can be found under
``/etc/ztpserver/ztpserver.conf``. (For format details, see top section
@https://docs.python.org/2/library/configparser.html).

The server can be started using a non-default global configuration file
- in order to do this, please use the ``--conf`` command line option:
e.g.

::

    (bash)# ztps --help
    usage: ztpserver [options]

    optional arguments:
      -h, --help            show this help message and exit
      --version, -v         Displays the version information
      --conf CONF, -c CONF  Specifies the configuration file to use
    (bash)# ztps --conf /var/ztps.conf

If the global configuration file is updated, then the server needs to be
restarted in order to pick up the new configuration.

Sections and attributes
'''''''''''''''''''''''

.. code-block:: ini

    [default]

    # Location of all ztps boostrap process data files
    # default=/var/lib/ztpserver
    data_root=<PATH>

    # UID used in the /nodes structure (serialnum is not supported yet)
    # default=systemmac
    identifier=<systemmac | serialnum> 

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

.. note::

    Configuration values can be overridden by setting
    environment variables, if the configuration attribute supports it.
    This is mainly used for testing and should not be used in production
    deployments. Configuration values that support environment overrides
    use the environ keyword, as shown below (from config.py):

.. code-block:: python

    runtime.add_attribute(StrAttr(
        name='data_root',
        default='/usr/share/ztpserver',
        environ='ZTPS_DEFAULT_DATAROOT'
    ))

In the above example, the ``data_root`` value is normally configured in
the [default] section as ``data_root``; however, if the environment
variable ``ZTPS_DEFAULT_DATAROOT`` is defined, it will take precedence.

The ZTPServer side components will be housed in a single directory
defined by the ``data_root`` variable in the global configuration file.
The directory location will vary depending on the configuration in
``/etc/ztpserver/ztperserver.conf``. The data\_root is loaded when ztps
is executed. The following directory structure is normally used:

.. code-block:: ini

    [data_root]
        /bootstrap
            - bootstrap
            - bootstrap.conf
        /nodes
            /<system id (MAC)>
                - startup-config
                - definition
                - pattern
                - .node
                - attributes
        /actions
        /files
        /definitions
        /resources
        /neighbordb

Bootstrap configuration
^^^^^^^^^^^^^^^^^^^^^^^

``[data_root]/bootstrap`` contains files that control the bootstrap
process on a node

-  **bootstrap** is the base bootstrap script which is going to be
   served to all clients in order to start and run the bootstrap
   process. Before serving the script to the clients, the server
   performs the following string substitution in the file: $SERVER → the
   value of ``server_url`` in the global configuration file

-  **bootstrap.conf** is a configuration file which defines the local
   logging configuration on the nodes (during the bootstrap process).
   The file is loaded on each request.

   e.g.

   .. code-block:: yaml

       logging:
           - destination: file:/tmp/ztps-log
               level: DEBUG
           - destination: ztps-server:1234
               level: CRITICAL
           - destination: 10.0.1.1:9000
               level: CRITICAL
       ...
       xmpp:
           username: ztps
           password: ztps
           domain: pcknapweed.lab.local
           rooms:
               - ztps-room1
               - ztps-room2
               ...

Node-specific configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``[data_root]/nodes`` contains node-specific configuration files.

Startup configuration
^^^^^^^^^^^^^^^^^^^^^

``startup-config`` provides a static startup configuration file. If this
file is present in a node’s folder, when the node sends a GET request to
``/nodes/<systemmac>``, the server will respond with a static definition
that includes:

-  a **replace\_config** action which will install the configuration
   file on the switch (see `actions <#actions>`__ section below for more
   on this)
-  all the **actions** from the local **definition** file (see
   definition section below for more on this) which have the
   ``always_execute`` attribute set to ``True``

Definition file
^^^^^^^^^^^^^^^

The definition file is the collection of actions which are going to be
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
    …

    attributes:                         # attributes at global scope
        <key>: <value>
        <key>: <value>
        <key>: <value>

Attributes
''''''''''

Attributes are either key/value pairs, key/dictionary pairs, key/list
pairs or key/reference pairs. They are all sent to the client in order
to be passed in as arguments to actions.

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

       **key/reference** attributes are identified by the fact that the
       value starts with the ‘$’ sign, followed by the name of another
       attribute. They are evaluated before being sent to the client

   here is an example:

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

The values of the attributes can be either strings, lists, dictionaries,
references to other attributes or functions\*. The supported functions
are:

-  **allocate(resource\_pool)** - allocate available resource from
   resource pool; the allocation is perform on the server side and the
   result of the allocation is passed to the client via the definition

.. note::

    Functions can only be used with string as arguments
    currently. See section on `add\_config <#actions>`__ action for
    examples.

Attributes can be defined in three places:

-  in the node’s attributes file (see below)
-  in the definition, at global scope
-  in the definition, at action scope

For key/value, key/list and and key/reference attributes, in case of
conflicts between the three scopes, the following tiebreaker rules are
applied in order to decide which value to send to the client:

1. action scope in the definition takes precedence
2. ``attributes`` file comes next
3. global scope in the definition comes last

For key/dict attributes, in case of conflicts between the scopes, the
dictionaries are merged. In case of dictionary key conflicts, the same
tiebreaker rules from above apply.

Pattern file
^^^^^^^^^^^^

The ``pattern`` file provides a statically typed pattern match which is
used to validate the node’s neighbors during the bootstrap process (if
topology validation is enabled). The pattern file can be either:

-  manually created OR
-  auto-generated by the server, when the node matches one of the
   patterns in ``neighbordb``. The pattern that is matched in
   ``neighbordb`` is written to this file and used for topology
   validation in subsequent re-runs of the bootstrap process.

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
definition, the server will log a message and either:

-  return 400 (BAD\_REQUEST) if topology validation is enabled
-  return 200 (OK) if topology validation is disabled

If topology validation is enabled, the following pattern can be used in
order to disable it locally for a node (the pattern from below will
match **any** node):

.. code-block:: yaml

    name: <pattern name>
    interfaces:
        - any: any:any   

Node details
^^^^^^^^^^^^

The ``.node`` file contains a cached copy of the node’s details that are
received during the POST request the node makes to ``/nodes (URI)``.
This cache is used to validate the node’s neighbors against the
``pattern`` file if topology validation is enabled (during the GET
request the node makes in order to retrieve its definition).

Attributes file
^^^^^^^^^^^^^^^

``attributes`` is a file which can be used in order to store attributes
associated with the node’s definition. This is especially useful
whenever multiple nodes share the same definition - in that case,
instead of having of edit each node’s definition in order to add the
attributes (at the global or action scope), all nodes can share the same
definition (which might be symlinked to their individual node folder)
and the user only has to create the attributes file for each node. The
``attributes`` file should be a valid key/value YAML file.

Actions
~~~~~~~

``[data_root]/actions`` contains all of the actions available for use in
definitions. More details about each action can be found at the top of
the corresponding Python file.

+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Action                 | Description                                                                                       | Required Attributes                                                  |
+========================+===================================================================================================+======================================================================+
| add\_config^           | Adds a section of config to the final startup-config file                                         | url                                                                  |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| copy\_file             | Copies a file from the server to the destination node                                             | src\_url, dst\_url, overwrite, mode                                  |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| install\_cli\_plugin   | Installs a new EOS CLI plugin and configures rc.eos                                               | url                                                                  |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| install\_extension     | Installs a new EOS extension                                                                      | extension\_url, autoload, force                                      |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| install\_image         | Validates and installs a specific version of EOS                                                  | url, version                                                         |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| replace\_config        | Sends an entire startup-config to the node (overrides add\_config)                                | url                                                                  |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| send\_email            | Sends an email to a set of recipients routed through a relay host. Can include file attachments   | smarthost, sender, receivers, subject, body, attachments, commands   |
+------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+

.. note::

    ^ *The ``add_config`` action supports applying block of
    EOS configuration commands to a node’s startup-config.*

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
marked in the template via the **$** symbol.

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

Note that in each of the examples from above, the template files are
just standard EOS configuration blocks.

Resources
~~~~~~~~~

``[data_root]/files`` contains all the files that actions might request
from the server. For example, ``[data_root]/files/images`` could contain
all EOS SWI files.

Definitions
~~~~~~~~~~~

``[data_root]/definitions`` contains a set of shared definition files
which can be associated with pattern in neighbordb (see neighbordb
section below) or symlink-ed from nodes’ folders.

Resource pools
~~~~~~~~~~~~~~

``[data_root]/resources`` contains global resource pools from which
attributes in definition can be allocated via the allocate(...)
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
null value will be replaced by the node’s system MAC address. Here is an
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

Neighbordb
~~~~~~~~~~

The ``neighbordb`` YAML file defines mappings between nodes descriptions
and nodes definitions. If a node does not already have a node
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
          node: <system_mac>
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

    Items are mandatory elements. Everything else is
    optional.

variables
^^^^^^^^^

This section allows for the definition of variables in neighbordb. The
variables can be used to match remote device and/or interface names
(``<system_name>``, ``<neighbor_port_name>`` above) for a node during
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
    defines a string that cannot be present in the node name

system\_mac
'''''''''''

MAC address of a node - supported formats:

-  1234.aaaa.4321
-  12:34:aa:aa:43:21
-  1234aaa4321

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
   -  Ethernet1/3-2/4 +
   -  Ethernet3-$ +
   -  Ethernet1/10-$ +

-  **All Interfaces on a Module**

   -  Ethernet1/$ +

.. note::

    *Available in future releases.*

system\_name:neighbor\_port\_name
'''''''''''''''''''''''''''''''''

Remote system an interfaces - supported values (STRING = any string
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

Examples
^^^^^^^^

Example #1: strongly typed definition with a strongly typed map
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    - name: standard leaf definition
      definition: leaf_template
      node: 001c73aabbcc
      interfaces:
        - Ethernet49: pod1-spine1:Ethernet1/1
        - Ethernet50: 
            device: pod1-spine2
            port: Ethernet1/1

In example #1, the topology map would only apply to a node with system
mac address equal to **001c73aabbcc**. The following interface map rules
apply:

-  Interface Ethernet49 must be connected to node pod1-spine1 on port
   Ethernet1/1
-  Interface Ethernet50 must be connected to node pod1-spine2 on port
   Ethernet1/1

Example #2: strongly typed definition with loose typed map
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    - name: standard leaf definition
      definition: leaf_template
      node: 001c73aabbcc
      interfaces:
        - any: regex('pod\d+-spine\d+'):Ethernet1/$
        - any: 
            device: regex('pod\d+-spine1')
            port: Ethernet2/3

In this example, the topology map would only apply to the node with
system mac address equal to **001c73aabbcc**. The following interface
map rules apply:

-  Any interface must be connected to node that matches the regular
   expression 'pod+-spine+' on port Ethernet1/$ (any port on module 1)
-  Any interface and not the interface selected in the previous step
   must be connected to a node that matches the regular expression
   'pod+-spine1' and is connected on port Ethernet2/3

Example #3: loose typed definition with a loose typed map
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    - name: standard leaf definition
      definition: dc-1/pod-1/leaf_template
      variables:
        - not_spine: excludes('spine')
        - any_spine: regex('spine\d+')
        - any_pod: includes('pod')
        - any_pod_spine: any_spine and any_pod*
      interfaces:
        - Ethernet1: $any_spine:Ethernet1/$
        - Ethernet2: $pod1-spine2:any
        - any: excludes('spine1'):Ethernet49
        - any: excludes('spine2'):Ethernet49
        - Ethernet49: 
            device: $not_spine
            port: Ethernet49
        - Ethernet50:
            device: excludes('spine')
            port: Ethernet50

    **Note:** \* Not yet supported

This example pattern could apply to any node that matches the interface
map. In includes the use of variables for cleaner implementation and
pattern re-use.

-  Variable not\_spine matches any node name where 'spine' doesn't
   appear in the string
-  Variable any\_spine matches any node name where the regular
   expression 'spine+' matches the name
-  Variable any\_pod matches any node name where that includes the name
   'pod' in it
-  **Variable any\_pod\_spine combines variables any\_spine and any\_pod
   into a complex variable that includes any name that matches the
   regular express 'spine+' and the name includes 'pod' (not yet
   supported)**
-  Interface Ethernet1 must be connected to a node that matches the
   any\_spine pattern and is connected on Ethernet1/$ (any port on
   module 1)
-  Interface Ethernet2 must be connected to node 'pod1-spine2' on any
   Ethernet port
-  Interface any must be connected to any node that doesn't have
   'spine1' in the name and is connected on Ethernet49
-  Interface any must be connected to any node that doesn't have
   'spine2' in the name and wasn't already used and is connected to
   Ethernet49
-  Interface Ethernet49 matches if it is connected to any node that
   matches the not\_spine pattern and is connected on port 49
-  Interface Ethernet50 matches if the node is connected to port
   Ethernet50 on any node whose name does not contain ‘spine’

Example #4: loosely typed definition with loosely typed map
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    - name: sample mlag definition
      definition: mlag_leaf_template
      variables:
        any_spine: includes('spine')
        not_spine: excludes('spine')
      interfaces:
        - Ethernet1: $any_spine:Ethernet1/$
        - Ethernet2: $any_spine:any
    - Ethernet3: none
    - Ethernet4: any
    - Ethernet5:
        device: includes('oob')
        port: any
    - Ethernet49: $not_spine:Ethernet49
        - Ethernet50: $not_spine:Ethernet50

This is a similar example to #3 that demonstrates how an MLAG pattern
might work.

-  Variable any\_spine defines a pattern that includes the word 'spine'
   in the name
-  Variable not\_spine defines a pattern that matches the inverse of
   any\_spine
-  Interface Ethernet1 matches if it is connected to any\_spine on port
   Ethernet1/$ (any port on module 1)
-  Interface Ethernet2 matches if it is connected to any\_spine on any
   port
-  Interface 3 matches so long as there is nothing attached to it
-  Interface 4 matches so long as something is attached to it
-  Interface 5 matches if the node contains 'oob' in the name and is
   connected on any port
-  Interface49 matches if it is connected to any device that doesn't
   have 'spine' in the name and is connected on Ethernet50
-  Interface50 matches if it is connected to any device that doesn't
   have 'spine' in the name and is connected on port Ethernet50

Server-side implementation details
----------------------------------

NodeController POST FSM
~~~~~~~~~~~~~~~~~~~~~~~

|POST FSM| ###NodeController GET FSM |GET FSM|

Client-side implementation details
----------------------------------

Bootstrap exit codes
~~~~~~~~~~~~~~~~~~~~

Exit code
^^^^^^^^^

+-------------+--------------------------------------------------------------+
| Exit Code   | Explanation                                                  |
+=============+==============================================================+
| 1           | Server connection error                                      |
+-------------+--------------------------------------------------------------+
| 2           | Unable to enable eAPI                                        |
+-------------+--------------------------------------------------------------+
| 3           | Unexpected response from server                              |
+-------------+--------------------------------------------------------------+
| 4           | Node not found on server                                     |
+-------------+--------------------------------------------------------------+
| 5           | Server-side topology check failed                            |
+-------------+--------------------------------------------------------------+
| 6           | Action not found on server                                   |
+-------------+--------------------------------------------------------------+
| 7           | Startup config missing at the end of the bootstrap process   |
+-------------+--------------------------------------------------------------+
| 8           | Action failed                                                |
+-------------+--------------------------------------------------------------+
| 9           | Invalid definition                                           |
+-------------+--------------------------------------------------------------+
| 10          | Invalid definition location received from server             |
+-------------+--------------------------------------------------------------+
| 11          | Other                                                        |
+-------------+--------------------------------------------------------------+
| 100         | Unable to install requests library (4.12.x)                  |
+-------------+--------------------------------------------------------------+

Action attributes
~~~~~~~~~~~~~~~~~

The bootstrap script will pass in as argument to the main method of each
action a special object called ‘attributes’. The only API the action
needs to be aware for this object is the ‘get’ method, which will return
the value of an attribute, as configured on the server:

-  the value can be local to a particular action or global
-  if an attribute is defined at both the local and global scopes, the
   local value takes priority
-  if an attribute is not defined at either the local or global level,
   then the ‘get’ method will return **None**

e.g. (action code)

.. code-block:: python

    def main(attributes):
        print attributes.get(‘software_image’)

Besides the values coming from the server, a couple of **special
entries**\ \* (always upper case) are also contained in the attributes
object:

1. ‘NODE’: a node object for making eAPI calls to localhost

   -  **API:**\ #
   -  api\_enable\_cmds(cmds, text\_format=False) // run eAPI commands
      from enable mode
   -  append\_startup\_config\_lines(lines)
   -  append\_rc\_eos\_lines(lines) // assumes bash code
      has\_startup\_config()
   -  log\_msg(msg, error=False)
   -  details() // get node details
   -  rc\_eos() // returns path for rc.eos
   -  flash() // returns path for flash
   -  startup\_config() // returns path for startup\_config
   -  retrieve\_url(url, path)

    | **Note:** \* *Only one for now.*

.. note::

    Object has other functionality as well and more of it
    could be documented and exposed in the future - this is the only one
    interesting for now.*

e.g. (action\_code)

.. code-block:: python

    def main(attributes):
        print attributes.get(‘NODE’).api_enable_cmds([‘show version’])

Bootstrap URLs
~~~~~~~~~~~~~~

1. DHCP response contains the **URL pointing to the bootstrap script**
2. The location of the bootstrap configuration server is hardcoded in
   the bootstrap script, using the SERVER global variable. The bootstrap
   script uses this base address in order to generate the **URL to use
   in order to GET the logging details**: ``BASE_URL/config`` e.g.

   .. code-block:: ini

       SERVER = ‘http://my-bootstrap-server’   # Note that the transport mechanism is
                                               # included in the URL

3. The bootstrap script uses the SERVER base address in order to compute
   the **URL to use in order to POST the node’s information:**
   ``BASE_URL/config``
4. The bootstrap script uses the ‘location’ header in the POST reply as
   the **URL to use in order to request the definition**
5. **Actions and resources URLs**\ & are computed by using the base
   address in the bootstrap script: BASE\_URL/actions/, BASE\_URL/files/

.. note::

    In future releases, the definition will contain an
    extra optional attribute for each action/resource which could be
    used in order to redirect the bootstrap client to another server in
    order to retrieve that resource. This will enable a more distributed
    model for serving ZTP actions and resources.*

Client - Server API
-------------------

URL Endpoints
~~~~~~~~~~~~~

+---------------+-------------------------------+
| HTTP Method   | URI                           |
+===============+===============================+
| GET^          | /bootstrap/config/{section}   |
+---------------+-------------------------------+
| GET           | /bootstrap/config             |
+---------------+-------------------------------+
| GET           | /bootstrap                    |
+---------------+-------------------------------+
| POST          | /nodes                        |
+---------------+-------------------------------+
| PUT           | /nodes/{id}                   |
+---------------+-------------------------------+
| GET           | /nodes/{id}                   |
+---------------+-------------------------------+
| GET           | /actions/{name}               |
+---------------+-------------------------------+
| GET           | /files/{filepath}             |
+---------------+-------------------------------+

    **Note:** ^ *Available in future releases.*

GET bootstrap script
^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap

    Returns the default bootstrap script

    **Response**

    .. code-block:: http

        Status: 200 OK
        Content-Type: text/x-python

.. note::

    For every request, the bootstrap controller on the
    ZTPServer will attempt to perform the following string replacement
    in the bootstrap script): **“$SERVER“ ---> the value of the
    “server\_url” variable in the server’s configuration file** This
    string-replacement will point the bootstrap client back to the
    server, in order to enable it to make additional requests for
    further resources.

-  if the ``server_url`` variable is missing in the server’s
   configuration file, 'http://ztpserver:8080' is used by default
-  if the ``$SERVER`` string does not exist in the bootstrap script, the
   controller will log a warning message and continue

GET logging configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap/config

    Returns the logging configuration from the server.

    **Request**

    .. sourcecode:: http

        GET /bootstrap/config HTTP/1.1
        Host: 
        Accept: 
        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Status: 200 OK
        Content-Type: application/json
        {
            “logging”*: [ {
                “destination”: “file:/<PATH>” | “<HOSTNAME OR IP>:<PORT>”,   //localhost enabled
                                                                            //by default
                “level”*:        <DEBUG | CRITICAL | ...>,
            } ]
        },
            “xmpp”*:{
                “server”:           <IP or HOSTNAME>,
                “port”:             <PORT>,                 // Optional, default 5222
                “username”*:        <USERNAME>,
                “domain”*:          <DOMAIN>,
                “password”*:        <PASSWORD>,
                “nickname”:         <NICKNAME>,             // Optional, default ‘username’
                “rooms”*:           [ <ROOM>, … ]                     
                }
            }
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

POST node details
^^^^^^^^^^^^^^^^^

Send node information to the server in order to check whether it can be
provisioned.

.. http:post:: /nodes

    **Request**

    .. sourcecode:: http

        Content-Type: application/json
        {
            “model”*:             <MODEL_NAME>, 
            “serialnumber”*:      <SERIAL_NUMBER>, 
            “systemmac”*:         <SYSTEM_MAC>,
            “version”*:           <INTERNAL_VERSION>, 

            “neighbors”*: {
                <INTERFACE_NAME(LOCAL)>: [ {
                    'device':             <DEVICE_NAME>, 
                    'remote_interface':   <INTERFACE_NAME(REMOTE)>
                } ]
            }, 
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    **Response**

    .. sourcecode:: http 

        Status: 201 Created
        Content-Type: text/html
        Location: <url>

        Status: 409 Conflict
        Content-Type: text/html
        Location: <url>

        Status: 400 Bad Request
        Content-Type: text/html

    :statuscode 201: Created
    :statuscode 409: Conflict
    :statuscode 400: Bad Request

GET definition
^^^^^^^^^^^^^^

Request definition from the server.

.. http:get:: /nodes/(ID)

    **Request**

    .. sourcecode:: http

        Content-Type: application/json
        {
            “model”*:             <MODEL_NAME>, 
            “serialnumber”*:      <SERIAL_NUMBER>, 
            “systemmac”*:         <SYSTEM_MAC>,
            “version”*:           <INTERNAL_VERSION>, 

            “neighbors”*: {
                <INTERFACE_NAME(LOCAL)>: [ {
                    'device':             <DEVICE_NAME>, 
                    'remote_interface':   <INTERFACE_NAME(REMOTE)>
                } ]
            }, 
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    **Response**

    .. sourcecode:: http

        Status: 200 OK
        Content-Type: application/json
        {
            “name”*: <DEFINITION_NAME>

            “actions”*: [{ “action”*:         <NAME>*,
                        “description”:     <DESCRIPTION>,
                        “onstart”:         <MESSAGE>,
                        “onsuccess”:       <MESSAGE>,
                        “onfailure”:       <MESSAGE>,
                        “always_execute”:  [True, False],
                        “attributes”: { <KEY>: <VALUE>,
                                        <KEY>: { <KEY> : <VALUE>},
                                        <KEY>: [ <VALUE>, <VALUE> ]
                                        }
                        },...]
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    :statuscode 400: Bad Request
    :statuscode 404: Not Found

GET action
^^^^^^^^^^

.. http:get:: /actions/(NAME)

I   Request action from the server.

    **Request**

    .. sourcecode:: http

        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Content-Type: text/x-python

    :statuscode 200: OK
    :statuscode 400: Bad Request
    :statuscode 404: Not Found

    Status: 200 OK
    Content-Type: text/plain
    <PYTHON SCRIPT>

    Status: 200 Bad request
    Content-Type: text/x-python

GET resource
^^^^^^^^^^^^

.. http:get::  /files/(RESOURCE_PATH)

    Request action from the server.

    **Request**

    .. sourcecode:: http

        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Status: 200 OK
        Content-Type: text/plain
        <resource>

    :statuscode 200: OK
    :statuscode 404: Not Found


.. |POST FSM| image:: https://raw.githubusercontent.com/arista-eosplus/ztpserver/develop/tree/gh-pages/images/NodeControllerPOST-FSM.png
.. |GET FSM| image:: https://raw.githubusercontent.com/arista-eosplus/ztpserver/develop/tree/gh-pages/images/NodeControllerGET-FSM.png
