Examples
========

.. contents:: :local:

.. _global_config:

Global configuration file
`````````````````````````

.. code-block:: ini

    [default]
    # Location of all ztps boostrap process data files
    data_root = /usr/share/ztpserver
    
    # UID used in the /nodes structure (serialnumber or systemmac)
    identifier = serialnumber
    
    # Server URL to-be-advertised to clients (via POST replies) during the bootstrap process
    server_url = http://172.16.130.10:8080
    
    # Enable local logging
    logging = True
    
    # Enable console logging
    console_logging = True
    
    # Globally disable topology validation in the bootstrap process
    disable_topology_validation = False
    
    [server]
    # Note: this section only applies to using the standalone server.  If
    # running under a WSGI server, these values are ignored
    
    # Interface to which the server will bind to (0:0:0:0 will bind to
    # all available IPv4 addresses on the local machine)
    interface = 172.16.130.10
    
    # TCP listening port
    port = 8080
    
    [ files]
    # Path for the files directory (overriding data_root/files)
    folder = files
    path_prefix = /usr/share/ztpserver
    
    [actions]
    # Path for the actions directory (overriding data_root/actions)
    folder = actions
    path_prefix = /usr/share/ztpserver
    
    [bootstrap]
    # Path for the bootstrap directory (overriding data_root/bootstrap)
    folder = bootstrap
    path_prefix = /usr/share/ztpserver
    
    # Bootstrap filename
    filename = bootstrap
    
    [neighbordb]
    
    # Neighbordb filename (file located in data_root)
    filename = neighbordb

.. _dynamic_neighbordb_example:

Dynamic neighbordb or pattern file
``````````````````````````````````

.. code-block:: yaml

    ---
    patterns:
    #dynamic sample
      - name: dynamic_sample
        definition: tor1
        interfaces:
          - Ethernet1: spine1:Ethernet1
          - Ethernet2: spine2:Ethernet1
          - any: ztpserver:any

      - name: dynamic_sample2
        definition: tor2
        interfaces:
          - Ethernet1: spine1:Ethernet2
          - Ethernet2: spine2:Ethernet2
          - any: ztpserver:any

.. _static_neighbordb_example:

Static neighbordb and /node/<unique-id>/pattern file
````````````````````````````````````````````````````
.. code-block:: yaml

    ---
    patterns:
    #static sample
      - name: static_node
        node: 000c29f3a39g
        interfaces:
          - any: any:any

.. _dynamic_definition_example:

Sample dynamic definition file
``````````````````````````````
.. code-block:: yaml

    ---
    actions:
      -
        action: install_image
        always_execute: true
        attributes:
          url: files/images/vEOS.swi
          version: 4.13.5F
        name: "validate image"
      -
        action: add_config
        attributes:
          url: files/templates/ma1.template
          variables:
            ipaddress: allocate('mgmt_subnet')
        name: "configure ma1"
      -
        action: add_config
        attributes:
          url: files/templates/system.template
          variables:
            hostname: allocate('tor_hostnames')
        name: "configure global system"
      -
        action: add_config
        attributes:
          url: files/templates/login.template
        name: "configure auth"
      -
        action: add_config
        attributes:
          url: files/templates/ztpprep.template
        name: "configure ztpprep alias"
      -
        action: add_config
        attributes:
          url: files/templates/snmp.template
          variables: $variables
        name: "configure snmpserver"
      -
        action: add_config
        attributes:
          url: files/templates/configpush.template
          variables: $variables
        name: "configure config push to server"
      -
        action: copy_file
        always_execute: true
        attributes:
          dst_url: /mnt/flash/
          mode: 777
          overwrite: if-missing
          src_url: files/automate/ztpprep
        name: "automate reload"
    attributes:
      variables:
        ztpserver: 172.16.130.10
    name: tora

.. _template_example:

Sample templates
````````````````
.. code-block:: yaml

    #login.template
    #::::::::::::::
    username admin priv 15 secret admin

.. code-block:: yaml

    #ma1.template
    #::::::::::::::
    interface Management1
      ip address $ipaddress
      no shutdown

.. code-block:: yaml

    #hostname.template
    #::::::::::::::
    hostname $hostname

.. _resources_example:

Sample resources 
````````````````
::

    #mgmt_subnet
    #::::::::::::::
    192.168.100.210/24: null
    192.168.100.211/24: null
    192.168.100.212/24: null
    192.168.100.213/24: null
    192.168.100.214/24: null

::

    #tor_hostnames
    #::::::::::::::
    veos-dc1-pod1-tor1: null
    veos-dc1-pod1-tor2: null
    veos-dc1-pod1-tor3: null
    veos-dc1-pod1-tor4: null
    veos-dc1-pod1-tor5: null

.. _mode_examples:

Mode Examples
``````````````

Example #1: strongly typed definition with a strongly typed map
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    ---
    - name: standard leaf definition
      definition: leaf_template
      node: ABC12345678
      interfaces:
        - Ethernet49: pod1-spine1:Ethernet1/1
        - Ethernet50: 
            device: pod1-spine2
            port: Ethernet1/1

In example #1, the topology map would only apply to a node with serial number,
the default ID, equal to **ABC12345678**. The following interface map rules
apply:

-  Interface Ethernet49 must be connected to node pod1-spine1 on port
   Ethernet1/1
-  Interface Ethernet50 must be connected to node pod1-spine2 on port
   Ethernet1/1

Example #2: strongly typed definition with loose typed map
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    ---
    - name: standard leaf definition
      definition: leaf_template
      node: 001c73aabbcc
      interfaces:
        - any: regex('pod\d+-spine\d+'):Ethernet1/$
        - any: 
            device: regex('pod\d+-spine1')
            port: Ethernet2/3

In this example, the topology map would only apply to the node with
system mac address equal to **001c73aabbcc**. This requires that identifier be
set to systemmac in the global ztpserver.conf file. The following interface
map rules apply:

-  Any interface must be connected to node that matches the regular
   expression 'pod+-spine+' on port Ethernet1/$ (any port on module 1)
-  Any interface and not the interface selected in the previous step
   must be connected to a node that matches the regular expression
   'pod+-spine1' and is connected on port Ethernet2/3

Example #3: loose typed definition with a loose typed map
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    ---
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

**Note:** \* In a future release.

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

    ---
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


More examples
`````````````

Additional ZTPServer file examples are available on GitHub at the `ZTPServer Demo <https://github.com/arista-eosplus/ztpserver-demo>`_.

