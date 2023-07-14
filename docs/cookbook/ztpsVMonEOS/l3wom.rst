ZTPServer VM on EOS in a L3WOM
==============================

.. The line below adds a local TOC

.. contents:::local:
  :depth: 1

Files Needed
------------

* ``ztps.vmdk``     : the VM disk image for the ZTPServer VM
* ``startup-config``: a text file (with no extension)
* ``ztps.sh``       : a bash shell script
* ``ztps.xml``      : an xml file
* ``dhcpd.conf``    : a text file for Linux dhcpd configuration
* ``dhcpd.rpm``     : a DHCP server RPM to be installed on EOS
* ``ztps_daemon``   : a python script
* ``fullrecover``   : an empty text file (with no extension)
* ``boot-config``   : a text file (with no extension); contains a single line: ``SWI=flash:EOS.swi``
* ``boot-extention``: a text file (with no extention); contains a single like: ``dhcpd.rpm``
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

* ``interface Loopback2``         : need a loopback interface on the same subnet as the VM
* ``daemon ztps``                 : used to run the ``ztps.daemon`` python script in the background
* ``event-handler ztps``          : used to start the shell script ``ztps.sh``
* ``virtual-machine ztps``        : used to start the ZTPServer VM on EOS
* ``management api http-commands``: need to enable eAPI for ``daemon ztps`` to function

.. code-block:: console

  interface Loopback2
    ip address 172.16.130.253/24

  daemon ztps
    command /mnt/flash/ztps_daemon &

  event-handler ztps
    trigger on-boot
    action bash /mnt/flash/ztps.sh &
    delay 300

  virtual-machine ztps
    config-file flash:/ztps.xml
    enable

  management api http-commands
    protocol http localhost
    no shutdown

Explanation
^^^^^^^^^^^
The ``event-handler ztps`` is triggered on-boot to kickstart the shell script ``ztps.sh``.  There is a delay of 300 seconds before the script will be executed, to make sure all the necessary systems are in place before we run the script.  For details of the script please see the ``ztps.sh`` section.

The ``management api http-commands`` section enables Arista eAPI on the host swithc; eAPI is leveraged by the ``ztps_daemon``.  eAPI can be accessed remotely via http or https, or it can be accessed locally via http, or by binding to a UNIX socket (only available on 4.14.5F onward).  Since the daemon is a script that runs locally, we can either enalbe eAPI on the localhost via http (if you are running 4.14.5F or later), or we can just enable eAPI over https (this will require authentication).

The ``daemon ztps`` section runs a python script in the back ground as a daemon to restart DHCPD whenever an interface comes up.

For details of the shell script ``ztps.sh`` and the python script ``ztps_daemon`` please refer to the corresponding sectio below.

.. note:: The loopback interface is only needed if you plan to bootstrap a L3 ECMP fabric without a management network.  In this scenario, the loopback address needs to be advertised in the ECMP routing protocol to enable connectivity for the downstream deviecs in the fabric.

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

  # Enable ip.forwarding
  sudo sysctl net.ipv4.conf.all.forwarding=1
  sudo sysctl net.ipv4.ip_forward=1

  logger -t "ZTPS" -p local0.info "ip.forwarding enabled"

  # Move the DHCP server RPM to the appropriate folder on EOS for installation
  # Move the dhcpd.conf file to the appropriate folder
  sudo cp /mnt/flash/dhcp-4.2.0-23.P2.fc14.i686.rpm /mnt/flash/.extensions/dhcpd.rpm
  sudo cp /mnt/flash/dhcpd.conf /etc/dhcp/
  sudo /usr/sbin/dhcpd
  sleep 5

  #make sure dhcpd is running before we continue
  ps aux | grep "dhcpd" | grep -v grep
  if [ $? -eq 0 ]
  then
  {
  logger -t "ZTPS" -p local0.info "DHCPD is running. Restart ZTPS VM."

  #Now lets restart the  ZTPS VM
  sudo echo -e "enable\nconfigure terminal\nvirtual-machine ztps restart\n" | FastCli -M -e -p 15

  logger -t "ZTPS" -p local0.info "ZTPS VM restarted"

  exit 0
  }
  else
    logger -t "ZTPS" -p local0.info "Looks like DHCPD didn't start. Lets sleep for a few seconds and try again"
    sleep 10
  fi

Explanation
^^^^^^^^^^^

In order to enable connectivity to the VM from both remotely and locally (from the host switch), a Linux bridge interface needs to be created and assigned an IP in the same subnet as the VM; Linux ``ip.forwarding`` also needs to be enabled in the kernel for the packets to be routed to the VM.

EOS does not come with dhcpd preinstalled, there a DHCP-Server RPM needs to be downloaded, installed and started.  Dowdload the RPM from `here <https://docs.google.com/a/arista.com/document/d/1fmhvousmZYr8Sidiv9rBf_PZDT-65QX0um215s_9K0c/edit#>`_ and rename it to ``dhcpd.rpm``. The RPM needs to be moved to the ``/mnt/flash/.extension`` location, and a ``boot-extension`` file, with the RPM specified, needs to be present in ``/mnt/flash`` in order for the RPM to be installed persistently after a reboot.

The ZTPServer VM needs to be restarted after the switch boots up.

.. note:: The ZTPServer VM needs to have its default gateway pointed to the br0 interface IP address.

.. End of ztps.sh


ztps.xml
--------

Objective
^^^^^^^^^

I want to prepare a KVM custom xml file to enable a VM on EOS.

Solution
^^^^^^^^

Key parts of the xml file to pay attention to:

* ``<domain type='kvm' id='1'>``          : in case multiple VMs are running on the system, make sure the configured ID is unique
* ``<driver name='qemu' type='vmdk'/>``   : make sure the type is ``vmdk``
* ``<source file='/mnt/usb1/ztps.vmdk'/>``: make sure the path is correct
* ``<mac address='08:00:27:85:0c:f8'/>``  : make sure this MAC matches the MAC address of the interface on the ZTPServer VM that you intend to use for connectivity
* ``<target dev='vnet0'/>``               : make sure the target device type is ``vnet0``

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
      <interface type='bridge'>
        <mac address='08:00:27:85:0c:f8'/>
        <source bridge='br0'/>
        <target dev='vnet0'/>
        <model type='e1000'/>
        <alias name='net0'/>
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

The target device type should be vnet0 to enable connectivity to the VM from both remotely and locally from the host switch.  Another choice here is the macvtap device type but this type prohibits connectivity for any locally routed packets (i.e. when the routing action to the VM takes place on the host switch).

.. End of ztps.xml


dhcpd.conf
----------

Objective
^^^^^^^^^

I want to prepare a dhcpd.conf file for running DHCPD on EOS.

Solution
^^^^^^^^

.. code-block :: console

  class "ARISTA" {
    match if substring(option vendor-class-identifier, 0, 6) = "Arista";
    option bootfile-name "http://172.16.130.10:8080/bootstrap";
  }

  # Example
  subnet 10.1.1.0 netmask 255.255.255.252 {
    option routers 10.1.1.1;
    default-lease-time 86400;
    max-lease-time 86400;
    pool {
          range 10.1.1.2 10.1.1.2;
          allow members of "ARISTA";
    }
  }

Explanation
^^^^^^^^^^^

The ``class "ARISTA"`` section defines a match criteria so that any subnet defition that uses this class would only allocate IPs if the requestor is an Arista device.  This class also defines a bootstrap file that will be downloaded to the requestor.

.. note:: The IP address and TCP port number defined for the bootfile needs to match the ZTPServer VM configuration.

The subnet section provides an example to show you how it can be defined.  If you are bootstrapping a L3 ECMP network without a management network, this section needs to be repeated for every p-to-p links connecting to every leaf switches.

.. note::  The ZTPServer VM also runs dhcpd, but in the scenario of L3 ECMP without a management network, we are unable to leverage that. This is because DHCP relay from the host switch to the VM is currently not supported in EOS.

.. End of dhcpd.conf


ztps_daemon
-----------

Objective
^^^^^^^^^

I want to create a python script that restarts DHCPD whenever an interface comes up.

Solution
^^^^^^^^

.. code-block:: python

  #!/usr/bin/env python3

  import jsonrpclib
  import os
  import time

  #PROTO = "https"
  #USERNAME = "admin"
  #PASSWORD = "admin"
  #HOSTNAME = "172.16.130.20"

  class EapiClient(object):
      '''
      Instantiate a Eapi connection client object
      for interacting with EAPI
    '''

    def __init__(self):
      # For EOS 4.14.5F and later, you can enable locally run scripts without needing to authenticate
      # If you are running earlier versions, just uncomment next line and also the CONSTANTS above
      #switch_url = '{}://{}:{}@{}/command-api'.format(PROTO, USERNAME, PASSWORD, HOSTNAME)
      switch_url = 'http://localhost:8080/command-api'
      self.client = jsonrpclib.Server(switch_url)

    def connected_interfaces(self):
      cmd = "show interfaces status connected"
      response = self.client.runCmds(1, [cmd])[0]
      connected_intfs = response['interfaceStatuses'].keys()
      return connected_intfs

  def restart_dhcpd(eapi):
      '''
      Monitor the connected interfaces.
      If there are newly connected interface(s), restart dhcpd
      '''
      connected_intfs = []

      while True:
          new_connected_intfs = eapi.connected_interfaces()
          for intf in new_connected_intfs:
              if intf not in connected_intfs:
                  os.system('sudo service dhcpd restart')

      connected_intfs = new_connected_intfs
      time.sleep(10)

  def main():
    eapi = EapiClient()
    restart_dhcpd(eapi)

  if __name__ == '__main__':
    try:
      main()
    except KeyboardInterrupt:
      pass

Explanation
^^^^^^^^^^^

DHCPD only binds to interfaces that are UP when the process started.  Since we are running DHCPD directly on the SPINE switch, there is no gaurantee that the interfaces connected to the LEAFs are up when DHCPD started.  Therefore, we need to run a script/daemon in the background to continuously check the connected interface status, and if new interfaces came up, DHCPD would be restarted to bind to the newly connected interfaces.

.. End of ztps_daemon
