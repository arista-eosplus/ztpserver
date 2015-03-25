ZTPServer VM on EOS in a L2L3WM
===============================

.. The line below adds a local TOC

.. contents:::local:
  :depth: 1

Files Needed
------------

* ``ztps.vmdk``     : the VM disk image for the ZTPServer VM
* ``startup-config``: a text file (with no extension)
* ``ztps.sh``       : a bash shell script
* ``ztps.xml``      : an xml file
* ``fullrecover``   : an empty text file (with no extension)
* ``boot-config``   : a text file (with no extension); contains a single line: ``SWI=flash:EOS.swi``
* ``EOS.swi``       : download an EOS image and rename it to ``EOS.swi``

.. End of Files Needed


ztps.vmdk
---------

Objective
^^^^^^^^^

I want to create a ZTPServer vmdk file to use on EOS.

Solution
^^^^^^^^

The ZTPServer vmdk file can be created using either methods below:
   1) Automatically Create a Full-Featured ZTPServer: https://github.com/arista-eosplus/packer-ZTPServer
   2) Create your own VM and install ZTPServer as intructed in the "Installation" section

Explanation
^^^^^^^^^^^

The turnkey solution detailed on the github will create a full featured ztps.vmdk by executing a single command.  The vmdk created using this method comes with certain parameters pre-defined (i.e. domain-name, root user credential, IP address, etc).  If desired, you can change these parameters by logging into the VM after it's created.

The second method requires more manual work compare to the first method, but may be more suitable if you already have a VM build to your needs and simply want to add ZTPServer to it.

.. End of ztps.vmdk


startup-config
--------------

Objective
^^^^^^^^^

I need to prepare a startup-config for the first SPINE switch to enable ZTPServer.

Solution
^^^^^^^^

Essential parts of the configuration:

* ``event-handler ztps``    : used to start the shell script ``ztps.sh``
* ``virtual-machine ztps``  : used to start the ZTPServer VM on EOS

.. code-block:: console

  interface Management1
    ip address 192.168.1.10/24

  event-handler ztps
    trigger on-boot
    action bash /mnt/flash/ztps.sh &
    delay 300

  virtual-machine ztps
    config-file flash:/ztps.xml
    enable

Explanation
^^^^^^^^^^^
The ``event-handler ztps`` is triggered on-boot to kickstart the shell script ``ztps.sh``.  There is a delay of 300 seconds before the script will be executed, to make sure all the necessary systems are in place before we run the script.  For details of the script please see the ``ztps.sh`` section.

External systems will connect to the VM via the management network.  The host switch will connect to the VM via the Linux bridge (See ``ztps.sh``).  Therefore in this scenario we will need to have 2 interfaces on the ZTPServer VM.

For details of the shell script ``ztps.sh`` please refer to the corresponding sectio below.

.. End of startup-config


ztps.sh
-------

Objective
^^^^^^^^^

I want to create a shell script to set up all the necessary environment for ZTPServer when the switch boots up.

Solution
^^^^^^^^

.. code-block:: console

  #!/bin/bash
  # This script is used with the event-handler so that on-boot, we will create linux bridge,
  #enable ip.forwarding, restart the ZTPS VM, and start DHCPD
  logger -t "ZTPS" -p local0.info "Starting the process for ZTPS VM deployment"

  # Create Linux Bridge
  sudo brctl addbr br0
  sudo ifconfig br0 up
  sudo ifconfig br0 172.16.130.254/24

  logger -t "ZTPS" -p local0.info "Linux Bridge created"

  #Now lets restart the  ZTPS VM
  sudo echo -e "enable\nconfigure terminal\nvirtual-machine ztps restart\n" | FastCli -M -e -p 15

  logger -t "ZTPS" -p local0.info "ZTPS VM restarted"

Explanation
^^^^^^^^^^^

In order to enable connectivity to the VM locally (from the host switch), a Linux bridge interface needs to be created and assigned an IP in the same subnet as one of the interfaces on the VM.

The ZTPServer VM needs to be restarted after the switch boots up.

.. note:: The ZTPServer VM needs to have its default gateway pointed to the default gateway of the management network.

.. End of ztps.sh


ztps.xml
--------

Objective
^^^^^^^^^

I want to prepare a KVM custom xml file to enable a VM on EOS.

Solution
^^^^^^^^

Key parts of the xml file to pay attention to:

* ``<domain type='kvm' id='1'>``          : id needs to be unique (if more than 1 VM)
* ``<driver name='qemu' type='vmdk'/>``   : make sure the type is ``vmdk``
* ``<source file='/mnt/usb1/ztps.vmdk'/>``: make sure the path is correct
* **Interface definition section**        :

  * MAC address in the xml need to match the MAC address of the interfaces on the ZTPServer VM.
  * The first interface type is direct and is mapped to ma1.  This is the interface that will be used for other switches to reach the VM.
  * The second interface type is bridge and is using Linux bridge.  This interface is solely used for local host switch to VM connectivity.

.. code-block :: console

  <domain type='kvm' id='1'>
    <name>ztps</name>
    <memory>1048576</memory>
    <currentMemory>1048576</currentMemory>
    <vcpu>1</vcpu>
    <os>
      <type arch='x86_64' machine='pc-i440fx-1.4'>hvm</type>
      <boot dev='hd'/>
    </os>
    <features>
      <acpi/>
      <apic/>
      <pae/>
    </features>
    <clock offset='utc'/>
    <on_poweroff>destroy</on_poweroff>
    <on_reboot>restart</on_reboot>
    <on_crash>restart</on_crash>
    <devices>
      <emulator>/usr/bin/qemu-system-x86_64</emulator>
      <disk type='file' device='disk'>
        <driver name='qemu' type='vmdk'/>
        <source file='/mnt/usb1/ztps.vmdk'/>
        <target dev='hda' bus='ide'/>
        <alias name='ide0-0-0'/>
        <address type='drive' controller='0' bus='0' unit='0'/>
      </disk>
      <controller type='ide' index='0'>
        <alias name='ide0'/>
        <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
      </controller>
      <interface type='direct'>
        <mac address='08:00:27:bc:d7:38'/>
        <source dev='ma1' mode='bridge'/>
        <target dev='macvtap0'/>
        <model type='e1000'/>
        <alias name='net0'/>
        <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
      </interface>
      <interface type='bridge'>
        <mac address='08:00:27:85:0c:f8'/>
        <source bridge='br0'/>
        <target dev='macvtap1'/>
        <model type='e1000'/>
        <alias name='net1'/>
        <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
      </interface>
      <serial type='pty'>
        <source path='/dev/pts/5'/>
        <target port='0'/>
        <alias name='serial0'/>
      </serial>
      <console type='pty' tty='/dev/pts/5'>
        <source path='/dev/pts/5'/>
        <target type='serial' port='0'/>
        <alias name='serial0'/>
      </console>
      <input type='tablet' bus='usb'>
        <alias name='input0'/>
      </input>
      <input type='mouse' bus='ps2'/>
      <graphics type='vnc' port='5900' autoport='no' listen='0.0.0.0'/>
      <video>
        <model type='vga' vram='8192' heads='1'/>
        <alias name='video0'/>
        <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
      </video>
      <memballoon model='virtio'>
        <alias name='balloon0'/>
        <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
      </memballoon>
    </devices>
  </domain>

Explanation
^^^^^^^^^^^

The interface definition section defines how the interface(s) of the VM should be initialized.  Since the vmdk already has interfaces defined/initialized, we have to use the same MAC address in the KVM definition file.

In the first interface definition we use ``interface type='direct'``.  In this configuration we map the first interface of the VM to the ``ma1`` interface directly, enabling connectivity to the VM from external of the host switch.  However, ``interface type='direct'`` does not allow for host switch to VM connectivity, therefore we need to define a second interface with ``interface type='bridge'`` and map that to the Linux bridge for this puspose.

The reason we could not just bridge ma1 with the Linux bridge (and therefore just use one interface to enable both local and external connectivity) is because when we enslave an interface to br0, that interface cannot have an IP address on it, otherwise the connectivity would break.

.. End of ztps.xml
