Hello World - A Simple Provisioning Example
===========================================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

**Introduction**

The following set of recipes will help you perform a basic provisioning task
using the ZTPServer. There are some assumptions:

* You have already installed the ZTPServer
* You have performed the basic configuration to define which interface and port the server will run on.
* You have a DHCP server running with ``option bootfile-name "http://<ZTPSERVER-URL>:<PORT>/bootstrap";`` `Sample config <https://github.com/arista-eosplus/packer-ztpserver/blob/master/Fedora/conf/dhcpd.conf>`_
* Your test (v)EOS node can receive DHCP responses
* Make sure the ztps process is not running

.. note:: If you would like to test this in a virtual environment, please see the
          `packer-ztpserver <https://github.com/arista-eosplus/packer-ztpserver>`_
          Github repo to learn how to automatically install a ZTPServer with all
          of the complementary services (DHCP, DNS, NTP, XMPP, and SYSLOG). Both
          Virtual Box and VMware are supported.


Prepare Your Switch for Provisioning
------------------------------------

Objective
^^^^^^^^^

I want to prepare my test device (vEOS or EOS) for use with the ZTPServer. This
will put your switch into ZTP Mode, so backup any configs you want to save.

Solution
^^^^^^^^

Log into your (v)EOS node, then:

.. code-block:: console

  switch-name> enable
  switch-name# write erase
  Proceed with erasing startup configuration? [confirm] y
  switch-name# reload now

Explanation
^^^^^^^^^^^

ZTP Mode is enabled when a switch boots and there is no startup-config (or it's empty) found in
``/mnt/flash/``.  Therefore, we use the ``write erase`` command to clear the current
startup-config and use ``reload now`` to reboot the switch. When the switch comes
up you will see it enter ZTP Mode and begin sending DHCP requests on all interfaces.

.. End of Prepare Your Switch for Provisioning


Add a Static Node Entry
-----------------------

Objective
^^^^^^^^^

I want to provision my switch based upon its System MAC Address.

Solution
^^^^^^^^

Log into your (v)EOS node to get its MAC Address. If it's in ZTP Mode, just log in
with username ``admin``:

.. code-block:: console

  switch-name> show version

.. note:: Copy the System MAC Address for later.

Confirm your ZTPServer Configuration will identify a node based upon its MAC:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``identifier`` and confirm it's set to ``systemmac``:

.. code-block:: console

  identifier = systemmac

Finally, let's create a nodes directory for this device:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the nodes directory, where all node information is stored
  admin@ztpserver:~# cd nodes

  # Create a directory using the MAC Address you found earlier
  admin@ztpserver:~# mkdir 001122334455


Explanation
^^^^^^^^^^^

A node is considered to be statically provisioned when a directory with its
System ID is already located in the ``nodes/`` directory.

Note that the System ID can be the node's System MAC Address or its Serial Number.
In this case we chose to use the ``systemmac`` since vEOS nodes don't have a
Serial Number by default.

Just adding this directory is not enough to provision the node. The remaining
recipes will finish off the task.

.. End of Add a Static Node Entry



Create a Startup-Config with Minimal Configuration
--------------------------------------------------

Objective
^^^^^^^^^

When my node is provisioned, I want it to be passed a static startup-config. This config will include
some basic Management network info including syslog and ntp. It will set
the admin user's password to admin, and enable eAPI.

Solution
^^^^^^^^

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the specific node directory that you created earlier
  admin@ztpserver:~# cd nodes/001122334455

  # Create a startup-config
  admin@ztpserver:~# vi startup-config

Copy and paste this startup-config, changing values where you see fit:

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

When the ZTPServer receives a request from your node to begin provisioning, it
will find the directory ``nodes/001122334455`` and know that this node is
statically configured. In this case, a ``startup-config`` must be present. In
practice, the ZTPServer tells the node to perform the ``config_replace`` action
with this file as the source.

.. End of Create a startup-config file with minimal configuration


Add Event Handler to Backup the startup-config to the ZTPServer
---------------------------------------------------------------

Objective
^^^^^^^^^

I want to backup the latest startup-config from my node so that if I make changes
or have to replace the node I have the latest copy.

.. note:: By adding this, the node will perform an HTTP PUT and overwrite the
          ``nodes/001122334455/startup-config`` file.

Solution
^^^^^^^^

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Move to the specific node directory that you created earlier
  admin@ztpserver:~# cd nodes/001122334455

  # Edit your startup-config
  admin@ztpserver:~# vi startup-config

Add the following lines to your startup-config, changing values where needed:

.. code-block:: console

  event-handler configpush
   trigger on-startup-config
   ! For default VRF, make sure to update the ztpserver url
   action bash export SYSMAC=`FastCli -p 15 -c 'show ver | grep MAC | cut -d" " -f 5' | sed 's/[.]*//g'`; curl http://<ZTPSERVER-URL>:<PORT>/nodes/$SYSMAC/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT
   ! For non-default VRF, update and use:
   ! action bash export SYSMAC=`FastCli -p 15 -c 'show ver | grep MAC | cut -d" " -f 5' | sed 's/[.]*//g'`; ip netns exec ns-<VRF-NAME> curl http://<ZTPSERVER-URL>:<PORT>/nodes/$SYSMAC/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT

Explanation
^^^^^^^^^^^

By adding this line to the startup-config, this configuration will be sent down
to the node during provisioning.  From that point onward, the node will perform
and HTTP PUT of the startup-config and the ZTPServer will overwrite the
startup-config file in the node's directory.

.. End of Add Event Handler to Backup the startup-config to the ZTPServer



Install a Specific (v)EOS Version
---------------------------------

Objective
^^^^^^^^^

I want a specific (v)EOS version to be automatically installed when I provision
my node.

.. note:: This assumes that you've already downloaded the desired (v)EOS image
          from `Arista <https://www.arista.com/en/support/software-download>`_.

Solution
^^^^^^^^

Let's create a place on the ZTPServer to host some SWIs:

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
  admin@ztpserver:~# cd nodes/001122334455

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

.. note:: The definition uses YAML syntax

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


.. End of Install a Specific (v)EOS Version


Start ZTPServer in Standalone Mode
----------------------------------

Objective
^^^^^^^^^

Okay, enough reading and typing; let's push some buttons!

Solution
^^^^^^^^

Let's run the ZTPServer in `Standalone Mode <http://ztpserver.readthedocs.org/en/master/startup.html#standalone-debug-server>`_
since this is just a small test. Login to your ZTPServer:

.. code-block:: console

  # Start the ZTPServer - console loggin will appear
  admin@ztpserver:~# ztps
  INFO: [app:115] Logging started for ztpserver
  INFO: [app:116] Using repository /usr/share/ztpserver
  Starting server on http://<ZTPSERVER-URL>:<PORT>

Explanation
^^^^^^^^^^^

The easiest way to run the ZTPServer is in Standalone Mode - which is done by
typing ``ztps`` in a shell. This will cause the configured interface and port to start listening
for HTTP requests. Your DHCP server will provide the node with ``option bootfile-name "http://<ZTPSERVER-URL>:<PORT>/bootstrap"``
in the DHCP response, which lets the node know where to grab the bootstrap script.

**A Quick Overview of the Provisioning Process for this Node**

 #. **GET /bootstrap**: The node gets the bootstrap script and begins executing it. The following requests are made while the bootstrap script is being executed.
 #. **GET /bootstrap/config**: The node gets the bootstrap config which contains XMPP and Syslog information for the node to send logs to.
 #. **POST /nodes**: The node sends information about itself in JSON format to the ZTPServer. The ZTPServer parses this info and finds the System MAC. It looks in the ``nodes/`` directory and finds a match.
 #. **GET /nodes/001122334455**: The node requests its definition and learns what resources it has to retrieve.
 #. **GET /actions/install_image**: The node retrieves the install_image script.
 #. **GET /files/images/vEOS_4.14.5F.swi**: The node retrieves the SWI referenced in the definition.
 #. **GET /meta/files/images/vEOS_4.14.5F.swi**: The node retrieves the checksum of the SWI for validation and integrity.
 #. **GET /actions/replace_config**: The node retrieves the replace_config script.
 #. **GET /nodes/001122334455/startup-config**: The node retrieves the startup-config we created earlier.
 #. **GET /meta/nodes/001122334455/startup-config**: The node retrieves the checksum of the startup-config.
 #. **Node Applies Config and Reboots**
 #. **PUT /nodes/001122334455/startup-config**: The node uploads its current startup-config.

.. End of Start ZTPServer in Standalone Mode
