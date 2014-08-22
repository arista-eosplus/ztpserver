Examples
========

.. contents:: Topics

.. _global_config:

Global configuration file
`````````````````````````

.. code-block:: ini

    [default]
    # Location of all ztps boostrap process data files
    data_root = /usr/share/ztpserver
    
    # UID used in the /nodes structure (serialnum is not supported yet)
    identifier = systemmac
    
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

Static neighbordb and /node/<MAC>/pattern file
``````````````````````````````````````````````
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

More examples
`````````````

Additional ZTPServer file examples are available on GitHub at the `ZTPServer Demo <https://github.com/arista-eosplus/ztpserver-demo>`_.

