Run ZTPServer as a VM on EOS
===========================================

.. The line below adds a local TOC

.. contents:::local:
  :depth: 1

**Introduction**

Bootstrapping network devices, much like bootstrapping servers, requires a server in place to handle that function.  Often, it is cumbersome to have that server ready before the network is up and running.  Therefore, it will be very convenient to have a server up and running, along with the first node in the network fabric, to handle bootstrapping for the rest of the infrastructure.

Arista EOS provides the capability to run VMs on top of EOS, therefore making the above scenario possible.  The following set of recipes will help you perform the necessary steps to streamline your data center network bootstrapping process:

* You can have everything prepared and stored on a USB key.
* Plug in the USB key to the first SPINE switch in the data center.
* The rest of the data center fabric will be bootstrapped automatically!

There are 3 different deployment topologies, and your network design should fall into one of them.  Each topology requires slightly different recipes, and they are explained in the following sections.

* **L2L3WM**  : a L2 MLAG or L3 ECMP fabric with an out-of-band management network (switches managed via the management port)
* **L2WOM**   : a L2 MLAG fabric without an out-of-band management network (switches managed in-band via SVI)
* **L3WOM**   : a L3 ECMP fabric without an out-of-band management network (switches managed in-band via loopback)

.. toctree::
   :maxdepth: 1

   ztpsVMonEOS/l2l3wm
   ztpsVMonEOS/l2wom
   ztpsVMonEOS/l3wom


Deployment Steps
----------------

Objective
^^^^^^^^^

I want to use a single USB key to bootstrap my entire data center fabric.

Solution
^^^^^^^^

Follow the steps below:

1) Obtain an USB key that's at least 4GB and format it with either MS-DOS or FAT file system
2) Copy all the files listed in the "Files Needed" section onto the USB key
3) Plug the USB key into the USB port on the first SPINE switch
4) Sit back and watch your data center network fabric bring itself up!

.. note:: All files and directories present on the USB flash drive will be copied to the switch.
          It is recommended that the USB drive contains only the three files listed above.

Explanation
^^^^^^^^^^^

The USB key method leverages the Arista Password Recovery mechanism.  When the ``fullrecover`` and ``boot-config`` file is present on the USB key, the system will check the timestamp on the ``boot-config`` file.If the timestamp is different, all files on the USB key will be copied to the flash on the switch, and the switch will be rebooted and come up with the ``startup-config`` and the ``EOS.swi`` included on the USB key.

.. End of Deployment Steps