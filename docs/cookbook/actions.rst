Actions
=======

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Add a Configuration Block to a Node
-----------------------------------

Objective
^^^^^^^^^

In order to keep your provisioning data modular, you may want to break apart
configuration blocks into small code blocks. You can use the ``add_config``
action to place a block on code on the node.

Solution
^^^^^^^^

**Example 1: Add a static block of configuration to your node**

First, create a template file with the desired configuration.

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Make sure you have a directory for templates
  admin@ztpserver:~# mkdir -p files/templates

  # Create a static config block
  admin@ztpserver:~# vi files/templates/east-dns.template

.. code-block:: console

  !
  ip name-server vrf default east.ns1.example.com
  !

Then add the ``add_config`` action to your definition:

.. code-block:: yaml

    ---
    actions:
      -
        action: add_config
        attributes:
          url: files/templates/east-dns.template
        name: "Add East DNS Server"


Explanation
^^^^^^^^^^^

Here we defined a simple action that adds configuration to the node during
provisioning. The ``url`` in this case is relative to ``[data_root]``/url. It's
important to realize that the ZTPServer does not compile these configuration
blocks into a startup-config and then send a single file to the node.  Rather,
the node executes each action independently, building the configuration in a
module fashion. If you are interested in performing variable substitution in your
templates to make them more flexible, see the next recipe.

.. note:: Please see the `add_config <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.add_config>`_
          documentation for more details.

.. end of Add a Configuration Block to a Node



Add Configuration to a Node Using Variables
-------------------------------------------

Objective
^^^^^^^^^

I want to keep my templates flexible by using variables. In some cases, I'd like
to assign a variable from a resource pool.

Solution
^^^^^^^^

First, create a template file with the desired configuration. In this recipe let's
configure interface Management1.

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Make sure you have a directory for templates
  admin@ztpserver:~# mkdir -p files/templates

  # Create a static config block
  admin@ztpserver:~# vi files/templates/ma1.template

Paste this config into the template:

.. code-block:: console

  !
  interface Management1
    ip address $ipaddress
    no shutdown
  !

Then add the ``add_config`` action to your definition:

.. code-block:: yaml

    ---
    actions:
      -
        action: add_config
        attributes:
          url: files/templates/ma1.template
          variables:
            ipaddress: allocate("mgmt_subnet")
        name: "Configure Ma1"

Then create a resource pool called mgmt_subnet:

.. code-block:: console

  # Create a resource pool
  admin@ztpserver:~# vi resources/mgmt_subnet

Paste the following into ``mgmt_subnet``:

.. code-block:: yaml

    192.0.2.10/24: null
    192.0.2.11/24: null
    192.0.2.12/24: null
    192.0.2.13/24: null

Explanation
^^^^^^^^^^^

This recipe ties a few different concepts together. From a high-level, the definition
contains an action, ``add_config``, which references a configuration block, ``ma1.template``.
Further, we use a variable, ``$ipaddress`` in the template file so that the template
can be used for all nodes being provisioned.  The final piece is the use of the
``allocate()`` plugin, which dynamically assigns a key from the associated
file-based resource pool.

In practice, when a node requests its definition the ZTPServer will execute the
``allocate("mgmt_subnet")`` plugin and assign a key from the pool.
The ZTPServer will then write the SYSTEM_ID as the value, overwriting ``null``.

If you wanted to use the assigned value elsewhere in the definition, simply call
``allocate(mgmt_subnet)`` and the plugin will not assign a new value, rather it
will return the key already assigned. Note that this is an implementation-detail
specific to this particular plugin - other plugins might vary (please read the 
associated documentation for each).

The result would look like:

.. code-block:: yaml

    192.0.2.10/24: <SYSTEM_ID>
    192.0.2.11/24: null
    192.0.2.12/24: null
    192.0.2.13/24: null

.. note:: Please see the `add_config <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.add_config>`_
          documentation for more details.

.. end of Add Configuration to a Node Using Variables



Replace Entire Startup-Config During Provisioning
-------------------------------------------------

Objective
^^^^^^^^^

I have a complete startup-config that I want to apply during provisioning. I want
to completely replace what's already on the node.

Solution
^^^^^^^^

First, create the startup-config with the desired configuration.

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Make sure you have a directory for templates
  admin@ztpserver:~# mkdir -p files/configs

  # Create a startup-config
  admin@ztpserver:~# vi files/configs/tor-startup-config

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


Then add the ``replace_config`` action to your definition:

.. code-block:: yaml

    ---
    actions:
      -
        action: replace_config
        attributes:
          url: files/configs/tor-startup-config
        name: "Replace entire startup-config"


Explanation
^^^^^^^^^^^

This action simply replaces the ``startup-config`` which lives in ``/mnt/flash/startup-config``.

.. note:: Please see the `replace_config <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.replace_config>`_
          documentation for more details.

.. end of Add a Configuration Block to a Node



Copy a File to a Node During Provisioning
-----------------------------------------

Objective
^^^^^^^^^

I want to copy a file to the node during the provisioning process and then
set its permissions.

Solution
^^^^^^^^

In this example we'll copy a python script to the node and set its permissions.

.. code-block:: yaml

  ---
  actions:
    -
      action: copy_file
      always_execute: true
      attributes:
        dst_url: /mnt/flash/
        mode: 777
        overwrite: if-missing
        src_url: files/automate/bgpautoinf.py
      name: "automate BGP peer interface config"

Explanation
^^^^^^^^^^^

Here we add the ``copy_file`` action to our definition. The attributes listed in
the action will be passed to the node so that it is able to retrieve the script
from ``[SERVER_URL]/files/automate/bgpautoinf.py``. Since we are using ``overwrite: if-missing``,
the action will only copy the file to the node if it does not already exist.

You could define the ``url`` as any destination the node can reach during provisioning - the
file does not need to exist on the ZTPServer.

.. note:: Please see the `copy_file <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.copy_file>`_
          documentation for more details.

.. end of Copy a File to a Node During Provisioning



Install a Specific EOS Image
----------------------------

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

  # Create a definition file
  admin@ztpserver:~# vi definitions/tor-definition

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

In this case we are hosting the SWI on the ZTPServer, so we just define the ``url`` in relation
to the ``data_root``. We could change the ``url`` to point to another server
altogether - the choice is yours. The benefit of hosting the file on the
ZTPServer is that we perform an extra checksum step to validate the integrity of
the file.

In practice, the node requests its definition during the provisioning process. It
sees that it's supposed to perform the ``install_image`` action, so it
requests the ``install_image`` python script. It then performs an HTTP GET for
the ``url``.  Once it has these locally, it executes the
`install_image <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.install_image>`_
script.


.. end of Install a specific EOS image





Install a Specific EOS Image without downgrading newer systems
--------------------------------------------------------------

Objective
^^^^^^^^^

I want a specific (v)EOS version to be automatically installed when I provision
my node but I don't want systems with newer EOS versions to be downgraded

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

  # Create a definition file
  admin@ztpserver:~# vi definitions/tor-definition

Add the following lines to your definition, changing values where needed.  Specifically note the ``downgrade: false`` attribute.

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_image
      attributes:
        downgrade: false
        url: files/images/vEOS_4.17.1F.swi
        version: 4.17.1F
      name: "Install 4.17.1F"

.. note:: The definition uses YAML syntax

Explanation
^^^^^^^^^^^

The difference between this recipe and the one, above, is setting the ``downgrade`` attribute to ``false``.  When downgrades are disabled, an image will only be copied if the running image is older than the image in the ZTP configuration.

.. end of Install a specific EOS image



Install an Extension
--------------------

Objective
^^^^^^^^^

I want to install an extension on my node automatically.

Solution
^^^^^^^^

Let's create a place on the ZTPServer to host the RPMs:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Create an images directory
  admin@ztpserver:~# mkdir -p files/rpms

  # SCP your SWI into the images directory, name it whatever you like
  admin@ztpserver:~# scp admin@otherhost:/tmp/myRPM.rpm files/rpms/myRPM.rpm

Now let's create a definition that performs the ``install_extension`` action:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Create a definition file
  admin@ztpserver:~# vi definitions/tor-definition

Add the following lines to your definition, changing values where needed:

.. code-block:: yaml

  ---
  name: static node definition
  actions:
    -
      action: install_extension
      always_execute: true
      attributes:
        url: files/rpms/myRPM.rpm
      name: "Install myRPM extension"

.. note:: The definition uses YAML syntax

Explanation
^^^^^^^^^^^

The ``install_extension`` will copy the RPM defined in the ``url`` parameter and
copy it to the default extension directory, ``/mnt/flash/.extensions``

.. note:: Please see the `install_extension <http://ztpserver.readthedocs.org/en/master/actions.html#module-actions.install_extension>`_
          documentation for more details.
