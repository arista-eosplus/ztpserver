Ansible - Bootstrap EOS
=======================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Introduction
------------
The following recipes will help you bootstrap Arista EOS switches for use with
Ansible. Please review the `Ansible-EOS <http://ansible-eos.readthedocs.org/en/master/overview.html#the-ansible-eos-role>`_
documentation to determine your preferred connection type: SSH or eAPI.

.. note:: Please contact us if you are interested in dynamically adding your
          nodes to Ansible Tower.  We have various examples that utilize the
          Tower API to add your node to a specific Tower inventory and/or group.

Bootstrap EOS for Ansible using SSH
-----------------------------------

Objective
^^^^^^^^^

I want to bootstrap an EOS node so that I can use Ansible to SSH to the node.

Solution
^^^^^^^^

.. note:: Prior to EOS 4.14.5, eAPI must be configured with HTTPS or HTTP and a
          flash:eapi.conf must be created for pyeapi or the eAPI credentials
          must be passed in the Ansible task using meta arguments.
          Starting with EOS 4.14.5, pyeapi can use unix-sockets to communicate
          with eAPI, locally.


**Step 1**  Gather Ansible Control Host SSH Key

First, store the Ansible Control Host SSH key on the ZTPServer (or make it available via URL).
When the ``configure_ansible_client`` action runs it will create a bash user on the
switch and put this key in ``~/.ssh/authorized_keys``.

In ``[DATA_ROOT]/files/ssh/key.pub``

.. code-block:: console

  ssh-rsa AAAAB3NzaC1yc....rest of public key......

**Step 2** Create a management IP resource pool

Reference this `recipe <http://ztpserver.readthedocs.org/en/develop/cookbook/actions.html#add-configuration-to-a-node-using-variables>`_
for an example.

**Step 3** Create eAPI configuration

In ``[DATA_ROOT]/files/templates/eapi.template``

**Option A** Using Unix Sockets (4.14.5+)

.. code-block:: console

  !
  management api http-commands
     no protocol https
     protocol unix-socket
     no shutdown
  !

**Option B** Using HTTPS

.. code-block:: console

  !
  management api http-commands
     no shutdown
  !

**Option C** Using HTTP

.. code-block:: console

  !
  management api http-commands
     no shutdown
     no protocol https
     protocol http
  !


**Step 4** Create a definition

Let's use the ``configure_ansible_client`` action to create the desired SSH user.

.. code-block:: yaml

  ---
  actions:
  -
    action: configure_ansible_client
    attributes:
      key: files/ssh/key.pub
      user: ansible
      passwd: password
      group: eosadmin
      root: "/persist/local/"
    name: "Configure Ansible"
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
      url: files/templates/eapi.template
    name: "Enable eAPI"


Explanation
^^^^^^^^^^^

Here we use the ``add_config`` action to load the switch with a standard
eAPI configuration as well as assign Management1 interface an IP address
allocated from the mgmt_subnet pool. Note that ZTPServer supports custom
allocate scripts that could dynamically assign an IP address from your own
IPAM. Also, the ``configure_ansible_client`` action is called. This client-side
action will create a bash user, with the specified name, and install any
SSH keys provided to ``~/.ssh/authorized_keys``. This is helpful because it takes
care of authentication between the Ansible Control host and the switch. The action
also writes to ``rc.eos`` to create this user on every boot (since it would normally be blown away).



Bootstrap EOS for Ansible using eAPI
------------------------------------

Objective
^^^^^^^^^

I want to bootstrap an EOS node so that I can use Ansible in connection:local
mode and connect to my switch via eAPI.

Solution
^^^^^^^^

**Step 1** Create a management IP resource pool

Reference this `recipe <http://ztpserver.readthedocs.org/en/develop/cookbook/actions.html#add-configuration-to-a-node-using-variables>`_
for an example.

**Step 2** Create eAPI configuration

In ``[DATA_ROOT]/files/templates/eapi.template``

**Option A** Using HTTPS

.. code-block:: console

  !
  management api http-commands
     no shutdown
  !

**Option B** Using HTTP

.. code-block:: console

  !
  management api http-commands
     no shutdown
     no protocol https
     protocol http
  !


**Step 3** Create a definition

.. code-block:: yaml

  ---
  actions:
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
      url: files/templates/eapi.template
    name: "Enable eAPI"


Explanation
^^^^^^^^^^^

Here we use the ``add_config`` action to load the switch with a standard
eAPI configuration as well as assign Management1 interface an IP address
allocated from the mgmt_subnet pool. Note that ZTPServer supports custom
allocate scripts that could dynamically assign an IP address from your own
IPAM.

.. note:: For more Action recipes see the Actions section.
