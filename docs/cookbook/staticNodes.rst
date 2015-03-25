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

.. code-block:: console

  switch-name> show version

.. note:: Copy down the System ID (System MAC Address or Serial Number).

Let's create a node directory for this device:

.. code-block:: console

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



Create a Startup-Config File
----------------------------

Objective
^^^^^^^^^

I want the node to receive a startup-config during provisioning.

Solution
^^^^^^^^

Create a file named ``startup-config`` in ``[data_root]/nodes/<SYSTEM_ID>/``.

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the node directory you created above.
  admin@ztpserver:~# cd nodes/<SYSTEM_ID>

  # Create/edit the startup-config file
  admin@ztpserver:~# vi startup-config

Place the desired configuration into the startup-config. Here's an example. Please
change values where you see fit:

.. code-block:: console

  !
  hostname test-node-1
  ip name-server vrf default <DNS-SERVER-IP>
  !
  ntp server <NTP-SERVER-IP>
  !
  username admin privilege 15 role network-admin secret admin
  !
  interface Management1
   ip address <MGMT-IP-ADDRESS>/<SUBNET>
  !
  ip access-list open
   10 permit ip any any
  !
  ip route 0.0.0.0/0 <DEFAULT-GW>
  !
  ip routing
  !
  management api http-commands
   no shutdown
  !
  banner login
  Welcome to $(hostname)!
  This switch has been provisioned using the ZTPServer from Arista Networks
  Docs: http://ztpserver.readthedocs.org/
  Source Code: https://github.com/arista-eosplus/ztpserver
  EOF
  !
  end

Explanation
^^^^^^^^^^^

A startup-config file is required when you statically provision a node.  The format
of the startup-config is the same as you are used to, which can be found on your
switch at file:startup-config (/mnt/flash/startup-config)

.. End of Create a Startup-Config File


Create a Pattern (Topology Validation enabled)
----------------------------------------------

Objective
^^^^^^^^^
I have created a static node directory and Topology Validation is
enabled, so I would like to make sure everything is wired up correctly before
provisioning a node.

.. note:: YAML syntax can be a pain sometimes. The indentation is done with
          spaces and not tabs.

Solution
^^^^^^^^

Create a file named ``pattern`` in ``[data_root]/nodes/<SYSTEM_ID>/``
and define the LLDP associations.

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the node directory you created above.
  admin@ztpserver:~# cd nodes/<SYSTEM_ID>

  # Create/edit the pattern file
  admin@ztpserver:~# vi pattern


**Example 1:** Match any neighbor

This pattern essentially disables Topology Validation.

.. code-block:: yaml

  ---
  name: Match anything
  interfaces:
    - any: any:any

**Example 2:** Match any interface on a specific neighbor

This pattern says, the node being provisioned must be connected to a neighbor
with hostname ``pod1-spine1`` but it can be connected to any peer interface.

.. code-block:: yaml

  ---
  name: Anything on pod1-spine1
  interfaces:
    - any: pod1-spine1:any

**Example 3:** Match specific interface on a specific neighbor

This pattern says, the node being provisioned must be connected to a neighbor
with hostname ``pod1-spine1`` on Ethernet1.

.. code-block:: yaml

  ---
  name: Anything on pod1-spine1
  interfaces:
    - any: pod1-spine1:Ethernet1

**Example 4:** Make sure I'm not connected to a node

This pattern is the same as Example #2, but we add another check to make sure the
node being provisioned is not connected to any spines in ``pod2``.

.. code-block:: yaml

  ---
  name: Not connected to anything in pod2
  interfaces:
    - any: pod1-spine1:any
    - any: regex('pod2-spine\d+'):none
    - none: regex('pod2-spine\d+'):any #equivalent to line above

**Example 5:** Using variables in the pattern

This pattern is similar to what you've seen above except we use variables
to make things easier.

.. code-block:: yaml

  ---
  name: Not connected to any spine in pod2
  variables:
    - not_pod2: regex('pod2-spine\d+')
  interfaces:
    - any: pod1-spine1:any
    - any: $not_pod2:none

Explanation
^^^^^^^^^^^

Pattern files are YAML-based and are the underpinnings of Topology Validation.
A node will not be successfully provisioned if it cannot pass all of the interface
tests contained within the pattern file. The examples above are just a small
sample of the complex associations you can create. Take a look at the
`neighbordb <http://ztpserver.readthedocs.org/en/master/config.html#dynamic-provisioning-neighbordb>`_
section to learn more.

.. note:: YAML can be a pain, and invalid YAML syntax will cause provisioning to
          fail.  You can make sure your syntax is correct by using a tool like
          `YAMLlint <http://www.yamllint.com>`_


.. End of Create a Pattern (if Topology Validation is enabled)


Create a Definition File
------------------------

Objective
^^^^^^^^^

Aside from sending the node a startup-config, I'd like to upgrade the node to
a specific v(EOS) version.

Solution
^^^^^^^^

These types of system changes are accomplished via the ``definition`` file.  The
definition is a YAML-based file with a section for each action that you
want to execute.

.. note:: Learn more about `Actions <http://ztpserver.readthedocs.org/en/master/config.html#actions>`_.

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Create an images directory
  admin@ztpserver:~# mkdir -p files/images

  # SCP your SWI into the images directory, name it whatever you like
  admin@ztpserver:~# scp admin@otherhost:/tmp/vEOS.swi files/images/vEOS_4.14.5F.swi

Now let's create a definition that performs the ``install_image`` action:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the specific node directory that you created earlier
  admin@ztpserver:~# cd nodes/<SYSTEM_ID>

  # Create a definition file
  admin@ztpserver:~# vi definition

Add the following lines to your definition, changing values where needed:

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_image
      always_execute: true
      attributes:
        url: files/images/vEOS_4.14.5F.swi
        version: 4.14.5F
      name: "Install 4.14.5F"


Explanation
^^^^^^^^^^^

The definition is where we list all of the `actions <http://ztpserver.readthedocs.org/en/master/config.html#actions>`_
we want the node to execute during the provisioning process. In this case we are
hosting the SWI on the ZTPServer, so we just define the ``url`` in relation
to the ``data_root``. We could change the ``url`` to point to another server
altogether - the choice is yours. The benefit in hosting the file on the
ZTPServer is that we perform an extra checksum step to validate the integrity of
the file.

In practice, the node requests its definition during the provisioning process. It
sees that it's supposed to perform the ``install_image`` action, so it
requests the ``install_image`` python script. It then performs an HTTP GET for
the ``url``.  Once it has these locally, it executes the
``install_image`` `script <https://github.com/arista-eosplus/ztpserver/blob/develop/actions/install_image>`_.

.. End of Create a Definition File



Create an Attributes File
-------------------------

Objective
^^^^^^^^^

I want to use variables in my definition and abstract the values to a unique file.
These variables will be sent down to the node during provisioning and be used while
the node is executing the actions listed in the definition.

Solution
^^^^^^^^

Create a file named ``attributes`` in ``[data_root]/nodes/<SYSTEM_ID>/``.

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the node directory you created above.
  admin@ztpserver:~# cd nodes/<SYSTEM_ID>

  # Move to the node directory you created above.
  admin@ztpserver:~# vi attributes

Here's the different type of ways to define the attributes:

**Example 1:** A simple key/value pair

.. code-block:: yaml

  ---
  ntp_server: ntp.example.com
  dns_server: ns1.example.com

**Example 2:** key/dictionary

.. code-block:: yaml

  ---
  system_config:
    ntp: ntp.example.com
    dns: ns1.example.com

**Example 3:** key/list (note the hyphens)

.. code-block:: yaml

  ---
  dns_servers:
    - ns1.example.com
    - ns2.example.com
    - ns3.example.com
    - ns4.example.com

**Example 4:** Referencing another variable

.. code-block:: yaml

  ---
  ntp_server: ntp.example.com
  other_var: $ntp_server

Borrowing from the definition recipe above, we can replace some values with
variables from the attributes file:

**nodes/<SYSTEM_ID>/definition**

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_image
      always_execute: true
      attributes:
        url: $swi_url
        version: $swi_version
      name: $swi_name

and the **nodes/<SYSTEM_ID>/attributes**

.. code-block:: yaml

  ---
  swi_url: files/images/vEOS_4.14.5F.swi
  swi_version: 4.14.5F
  swi_name: "Install 4.14.5F"


Explanation
^^^^^^^^^^^

The ``attributes`` file is optional.  The variables that are contained within it
are sent to the node during provisioning. In the final example above you can see
how the attributes file and definition work in concert. Note that the ZTPServer
performs variable substitution when the node requests the definition via
GET /nodes/<SYSTEM_ID>. By removing the static values from the definition, we can
use the same definition for multiple nodes (using symlink) and just create unique
attributes files in the node's directory.

It's important to note that these variables can exist in different places and
accomplish the same task.  In this recipe we created a unique attributes file,
which lives in the node's directory. You can also put these attributes directly
into the definition file like the example below.

**Example: At the global scope of the definition**

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_image
      always_execute: true
      attributes:
        url: $swi_url
        version: $swi_version
      name: $swi_name
  attributes:
    swi_url: files/images/vEOS_4.14.5F.swi
    swi_version: 4.14.5F
    swi_name: "Install 4.14.5F"

.. End of Create an Attributes File


Symlink to a Generic Definition
-------------------------------

Objective
^^^^^^^^^

I'd like to use the same definition for multiple static node directories without
manually updating each one.

Solution
^^^^^^^^

Create one definition in the ``[data_root]/definitions`` folder and create a symlink
to the specific ``[data_root]/nodes/<SYSTEM_ID>/`` folder.

**``[data_root]/definitions/static_node_definition**

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_image
      always_execute: true
      attributes:
        url: $swi_url
        version: $swi_version
      name: $swi_name

and the **nodes/<SYSTEM_ID>/attributes**

.. code-block:: yaml

  ---
  swi_url: files/images/vEOS_4.14.5F.swi
  swi_version: 4.14.5F
  swi_name: "Install 4.14.5F"

then create the symlink

.. code-block:: console

  # Go to your node's unique directory
  admin@ztpserver:~# cd /usr/share/ztpserver/nodes/<SYSTEM_ID>

  # Create the symlink
  admin@ztpserver:~# ln -s /usr/share/ztpserver/definitions/static_node_definition ./definition


Explanation
^^^^^^^^^^^

The steps above let you reuse a single definition file for many static nodes. Note
that the variables are located in the attributes file in the ``nodes/<SYSTEM_ID>/``
folder.

.. End of Symlink to a Generic Definition
