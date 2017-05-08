Advanced
========

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Configuration Management and prep for ZTR
-----------------------------------------

Objective
^^^^^^^^^

I want to automatically push the startup-config from each node to the
corresponding /nodes/ folder whenever changes are made on the node.

Solution
^^^^^^^^

The ZTPServer accepts HTTP PUT requests at ``nodes/<node_id>/startup-config``.
Therefore, we can configure and event-handler on the node during provisioning
which will perform this PUT anytime the startup-config is saved.

**1. Create event-handler template**

Choose the option that best fits your deployment. The variations are
Serial Number or System Mac Address, and Default VRF or Non-Default VRF.

Copy and paste the option text into a new template in:

.. code-block:: console

  # Go to your data_root - by default it's /usr/share/ztpserver
  admin@ztpserver:~# cd /usr/share/ztpserver

  # Make sure you have a directory for templates
  admin@ztpserver:~# mkdir -p files/templates

  # Create a static config block
  admin@ztpserver:~# vi files/templates/config-push.template

.. note:: Notice the ``$ztpserver``, ``$port`` and ``$vrf_name`` variables.
          You can hardcode these in the template or abstract these to the
          definition or attributes file (as shown in the next recipe).

**Option 1:** Using SystemMac and Default VRF

.. code-block:: console

  event-handler configpush
   trigger on-startup-config
   action bash export SYSMAC=`FastCli -p 15 -c 'show ver | grep MAC | cut -d" " -f 5' | sed 's/[.]*//g'`; curl http://$ztpserver:$port/nodes/$SYSMAC/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT

**Option 2:** Using SystemMac and Non-Default VRF

.. code-block:: console

  event-handler configpush
   trigger on-startup-config
   ! For non-default VRF, use:
   action bash export SYSMAC=`FastCli -p 15 -c 'show ver | grep MAC | cut -d" " -f 5' | sed 's/[.]*//g'`; sudo ip netns exec ns-$vrf_name curl http://$ztpserver:$port/nodes/$SYSMAC/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT

**Option 3:** Using Serial Number and Default VRF

.. code-block:: console

  event-handler configpush
   trigger on-startup-config
   ! For serial number, default VRF:
   action bash export SERIAL=`FastCli -p 15 -c 'show ver' | grep Serial | tr -s ' ' | cut -d ' ' -f 3 | tr -d '\r'`; curl http://$ztpserver:$port/nodes/$SERIAL/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT


**Option 4:** Using Serial Number and Non-Default VRF

.. code-block:: console

  event-handler configpush
   trigger on-startup-config
   ! For serial number, non-default VRF:
   action bash export SERIAL=`FastCli -p 15 -c 'show ver' | grep Serial | tr -s ' ' | cut -d ' ' -f 3 | tr -d '\r'`; sudo ip netns exec ns-$vrf_name curl http://$ztpserver:$port/nodes/$SERIAL/startup-config -H "content-type: text/plain" --data-binary @/mnt/flash/startup-config -X PUT

Zero-touch replatement (ZTR)
----------------------------

Objective
^^^^^^^^^

I replaced a switch with a new one and want it to provision with the same
configuration and, optionally, EOS version as the node it replaced.

Solution
^^^^^^^^

ZTPServer first looks for a pre-existing definition for a node in the
``<configdir>/nodes/<node-id>`` directory before trying to match through neighbordb, etc.
Thus, you can make ZTPServer think it has already seen this node by
renaming, linking or copying the old-node's directory to the new-node's
unique-id before powering the switch on for the first time.

Moving (renaming) or linking are most commonly used, however, making a
recursive copy will ensure that the last-known configuration of the previous
node remains stored as a backup.

.. code-block:: console

  cd /usr/share/ztpserver/nodes
  ln -s <old-node_id> <new-node_id>

.. End of ZTR
