<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [ZTPServer Setup - Packer.io VM Automation](#ztpserver-setup---packerio-vm-automation)
  - [Introduction](#introduction)
  - [Installation of Packer](#installation-of-packer)
    - [Creating a VM for use with VMWare Fusion](#creating-a-vm-for-use-with-vmware-fusion)
    - [Creating a VM for use with VirtualBox](#creating-a-vm-for-use-with-virtualbox)
  - [Setting up a Quick Demo](#setting-up-a-quick-demo)
  - [Troubleshooting](#troubleshooting)
    - [Gathering Diags](#gathering-diags)
    - [Potential Issues](#potential-issues)
      - [Error Detecting Host IP](#error-detecting-host-ip)
      - [Anaconda Installer Hangs at 'Installing Bootloader'](#anaconda-installer-hangs-at-installing-bootloader)
      - [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

#ZTPServer Setup - Packer.io VM Automation

##Introduction
You can use Packer.io to automate the creation of the ZTPServer VM.  By using this method, you can be sure that all of the required packages and dependencies are installed right out of the gate.  This procedure will:

* Create a VM with 7GB Hard Drive
* 2GB RAM
* Fedora 20 Minimal Install
* Python 2.7.5 with PIP
* Hostname ztps.ztps-test.com
    * eth0 (NAT) DHCP
    * eth1 (vmnet2) 172.16.130.10/24
* Firewalld disabled.
* Users
    * root/eosplus and ztpsadmin/eosplus
* DHCP installed with Option 67 configured (eth1 only)
* BIND DNS server installed with zone ztps-test.com
    * wildcard forward rule to 8.8.8.8 for all other queries
    * SRV RR for im.ztps-test.com
* rsyslog-ng installed; Listening on UDP and TCP (port 514)
* XMPP server configured for im.ztps-test.com
    * XMPP admin user ztpsadmin, passwd eosplus
* httpd installed and configured for ZTPServer (mod_wsgi) running on port 8080
* ZTPServer installed (with sameple files to get you running)

##Installation of Packer
> **Note:** This installation procedure requires internet access.

Packer.io automates the creation of the Virtual Machine.  Therefore, the first step is downloading and installing Packer.

1. Download the appropriate binaries - http://www.packer.io/downloads.html
2. Unzip and move to desired location eg ~/packer or /usr/local/share/ or /usr/local/bin/
3. Set ENV variable (or just put Packer somewhere the ```PATH``` is already pointing - ```echo $PATH```)
    * EG: in ~/.bash_login, add ```PATH=$PATH:/path/to/packer/files```
4. Run ```packer``` to make sure ```PATH``` is updated.

###Creating a VM for use with VMWare Fusion
> **Note:** The following procedure was tested using VMWare Fusion 6.0.3.
> **IMPORTANT** As you read above, eth1 will be placed on vmnet2. Therefore, you need to have this non-standard vmnet setup in your VMware environment.  We've created a script ```setup-fusion.sh```([link](https://github.com/arista-eosplus/ztpserver/blob/feature-packer/packer/vEOS/VMware/setup-fusion.sh)) to help add vmnets so that your setup will work with this basic install, as well as the demo found [here](https://github.com/arista-eosplus/ztpserver/tree/feature-packer/packer/vEOS/VMware).

1. Retrieve the EOS+ packer files by using the 'Download Zip' option here https://github.com/arista-eosplus/ztpserver/tree/feature-packer
2. ```cd``` to the location of the .json file.
3. This step is optional. If you want to use our demo files and get ZTPServer running quickly, then complete this step. ZTPServer will still run without these files.
    Download the following files and place them in the corresponding directories:
    * vEOS.swi - ```./files/images/vEOS.swi```
    * puppet-2.7.20-1.fc16.noarch.rpm - ```./files/puppet/puppet-2.7.20-1.fc16.noarch.rpm```
    * facter-1.6.17-1.fc16.i686.rpm - ```./files/puppet/facter-1.6.17-1.fc16.i686.rpm```
    * ruby-1.8.7.swix - ```./files/puppet/ruby-1.8.7.swix```
    * ruby-json-1.5.5.swix - ```./files/puppet/ruby-json-1.5.5.swix```
    * rubygems-1.3.7.swix - ```./files/puppet/rubygems-1.3.7.swix```

    Your directory should look like:
    ```
    [root]
       - ztps-fedora_20_x86_64.json
       - /http
           - ks-net.cfg
       - /conf
           - ...conf files
       - /scripts
           - setup.sh
       - /files
           - /images
               - vEOS.swi
           - /puppet
               - puppet-2.7.20-1.fc16.noarch.rpm
               - facter-1.6.17-1.fc16.i686.rpm
               - ruby-1.8.7.swix
               - ruby-json-1.5.5.swix
               - rubygems-1.3.7.swix
   ```
4. Run ```packer build --only=vmware-iso ztps-fedora_20_x86_64.json```
    You will see:
    ```
    phil:ztpserver phil$ packer build ztps-fedora_20_x86_64.json
    vmware-iso output will be in this color.

    ==> vmware-iso: Downloading or copying ISO
    vmware-iso: Downloading or copying: http://mirrors.xmission.com/fedora/linux/releases/20/Fedora/x86_64/iso/Fedora-20-x86_64-netinst.iso
    ==> vmware-iso: Creating virtual machine disk
    ==> vmware-iso: Building and writing VMX file
    ==> vmware-iso: Starting HTTP server on port 8608
    ==> vmware-iso: Starting virtual machine...
    ==> vmware-iso: Waiting 2s for boot...
    ==> vmware-iso: Connecting to VM via VNC
    ==> vmware-iso: Typing the boot command over VNC...
    ==> vmware-iso: Waiting for SSH to become available...
    ```
5. Once the ISO is downloaded, packer brings up a VMWare VM. The Anaconda installation will proceed without any user input.
6. After 10 minutes the OS installation will be complete, the VM will reboot, and you will be presented with a login prompt.  Resist the urge to log in and tinker - things are still being setup.
7. Meanwhile, you'll notice the packer builder ```ssh``` into the VM and begin working on updating, installing and configuring new services.
    ```
    phil:ztpserver phil$ packer build ztps-fedora_20_x86_64.json
    vmware-iso output will be in this color.

    ==> vmware-iso: Downloading or copying ISO
    vmware-iso: Downloading or copying: http://mirrors.xmission.com/fedora/linux/releases/20/Fedora/x86_64/iso/Fedora-20-x86_64-netinst.iso
    ==> vmware-iso: Creating virtual machine disk
    ==> vmware-iso: Building and writing VMX file
    ==> vmware-iso: Starting HTTP server on port 8574
    ==> vmware-iso: Starting virtual machine...
    ==> vmware-iso: Waiting 2s for boot...
    ==> vmware-iso: Connecting to VM via VNC
    ==> vmware-iso: Typing the boot command over VNC...
    ==> vmware-iso: Waiting for SSH to become available...
    ==> vmware-iso: Connected to SSH!
    ==> vmware-iso: Uploading the 'linux' VMware Tools
    ==> vmware-iso: Uploading conf => /tmp/packer
    ==> vmware-iso: Provisioning with shell script: scripts/setup.sh
    ... (shell script output)
    ```
8. After some extensive yumming (~5minutes), you will see:
    ```
    ==> vmware-iso: Gracefully halting virtual machine...
        vmware-iso: Waiting for VMware to clean up after itself...
    ==> vmware-iso: Deleting unnecessary VMware files...
        vmware-iso: Deleting: output-vmware-iso/startMenu.plist
        vmware-iso: Deleting: output-vmware-iso/vmware.log
        vmware-iso: Deleting: output-vmware-iso/ztps.plist
        vmware-iso: Deleting: output-vmware-iso/ztps.vmx.lck/M62713.lck
    ==> vmware-iso: Cleaning VMX prior to finishing up...
        vmware-iso: Detaching ISO from CD-ROM device...
    ==> vmware-iso: Compacting the disk image
    Build 'vmware-iso' finished.

    ==> Builds finished. The artifacts of successful builds are:
    --> vmware-iso: VM files in directory: output-vmware-iso
    ```
9. You now have a full-featured ZTPServer.
10. Log into the server with ```root``` and password ```eosplus```. Simply type ```ztps``` to start the ztpserver.


###Creating a VM for use with VirtualBox
> **Note:** The following procedure was tested using VirtualBox 4.3.12.

> **IMPORTANT:** Regarding VirtualBox networks. The default setup places eth1 on vboxnet2. This might not be created in your Virtual Box environment.  
Therefore, open Vbox and open the General Settings/Preferences menu. Click on the **Network** tab. Click on **Host-only Networks.**
Add or Modify vboxnet2.  Configure the IP Address for 172.16.130.1, the Netmask 255.255.255.0 and turn off the DHCP server.

1. Retrieve the EOS+ packer files by using the 'Download Zip' option here https://github.com/arista-eosplus/ztpserver/tree/feature-packer
2. ```cd``` to the location of the .json file.
3. This step is optional. If you want to use our demo files and get ZTPServer running quickly, then complete this step.  ZTPServer will still run without these files.
    Download the following files and place them in the corresponding directories:
    * vEOS.swi - ```./files/images/vEOS.swi```
    * puppet-2.7.20-1.fc16.noarch.rpm - ```./files/puppet/puppet-2.7.20-1.fc16.noarch.rpm```
    * facter-1.6.17-1.fc16.i686.rpm - ```./files/puppet/facter-1.6.17-1.fc16.i686.rpm```
    * ruby-1.8.7.swix - ```./files/puppet/ruby-1.8.7.swix```
    * ruby-json-1.5.5.swix - ```./files/puppet/ruby-json-1.5.5.swix```
    * rubygems-1.3.7.swix - ```./files/puppet/rubygems-1.3.7.swix```

    Your directory should look like:
    ```
    [root]
       - ztps-fedora_20_x86_64.json
       - /http
           - ks-net.cfg
       - /conf
           - ...conf files
       - /scripts
           - setup.sh
       - /files
           - /images
               - vEOS.swi
           - /puppet
               - puppet-2.7.20-1.fc16.noarch.rpm
               - facter-1.6.17-1.fc16.i686.rpm
               - ruby-1.8.7.swix
               - ruby-json-1.5.5.swix
               - rubygems-1.3.7.swix
    ```
4. Run ```packer build --only=virtualbox-iso ztps-fedora_20_x86_64.json``` for VirtualBox
    You will see:
    ```
    phil:Fedora phil$ packer build --only=virtualbox-iso ztps-fedora_20_x86_64.json
    virtualbox-iso output will be in this color.

    ==> virtualbox-iso: Downloading or copying Guest additions checksums
        virtualbox-iso: Downloading or copying: http://download.virtualbox.org/virtualbox/4.3.12/SHA256SUMS
    ==> virtualbox-iso: Downloading or copying Guest additions
        virtualbox-iso: Downloading or copying: http://download.virtualbox.org/virtualbox/4.3.12/VBoxGuestAdditions_4.3.12.iso
    ==> virtualbox-iso: Downloading or copying ISO
        virtualbox-iso: Downloading or copying: http://mirrors.xmission.com/fedora/linux/releases/20/Fedora/x86_64/iso/Fedora-20-x86_64-netinst.iso
    ```
5. Once the ISO is downloaded, packer brings up a VBox VM. The installation will proceed without any user input.
6. After a few minutes the OS installation will be complete, the VM will reboot, and you will be presented with a login prompt.  Resist the urge to log in and tinker - things are still being setup.
7. Meanwhile, you'll notice the packer builder ```ssh``` into the VM and begin working on updating, installing and configuring new services.
    ```
    ==> virtualbox-iso: Waiting for SSH to become available...
    ==> virtualbox-iso: Connected to SSH!
    ==> virtualbox-iso: Uploading VirtualBox version info (4.3.12)
    ==> virtualbox-iso: Uploading VirtualBox guest additions ISO...
    ==> virtualbox-iso: Uploading conf => /tmp/packer
    ==> virtualbox-iso: Uploading files => /tmp/packer
    ==> virtualbox-iso: Provisioning with shell script: scripts/setup.sh
        virtualbox-iso: + yum -y install deltarpm
      ... (shell script output)
    ```
8. After some extensive yumming (<5minutes), you will see:
    ```
    ==> virtualbox-iso: Gracefully halting virtual machine...
        virtualbox-iso:
        virtualbox-iso: Broadcast message from root@ztps.ztps-test.com on pts/0 (Tue 2014-06-17 08:44:25 EDT):
        virtualbox-iso:
        virtualbox-iso: The system is going down for power-off NOW!
        virtualbox-iso:
    ==> virtualbox-iso: Preparing to export machine...
        virtualbox-iso: Deleting forwarded port mapping for SSH (host port 3213)
    ==> virtualbox-iso: Exporting virtual machine...
        virtualbox-iso: Executing: export ztps-fedora-20-x86_64-2014-06-17T12:29:58Z --output output-virtualbox-iso/ztps-fedora-20-x86_64-2014-06-17T12:29:58Z.ovf
    ==> virtualbox-iso: Unregistering and deleting virtual machine...
    Build 'virtualbox-iso' finished.

    ==> Builds finished. The artifacts of successful builds are:
    --> virtualbox-iso: VM files in directory: output-virtualbox-iso
    Build 'vmware-iso' finished.
    ```
9. You now have a full-featured ZTPServer.
10. Log into the server with ```root``` and password ```eosplus```. Simply type ```ztps``` to start the ztpserver.


##Setting up a Quick Demo
As part of the installation above, sample files were copied from the ztpserver-demo repo and placed into the necessary locations ( /etc/ztpserver/ and /usr/share/ztpserver).  Follow the steps below to create a quick demo:

1. type ```cd /usr/share/ztpserver/nodes```.
2. copy the default spine config to a new node that has the MAC address of your local vEOS instance. ```mv 005056761aae <local spine MAC>```.
3. start ztpserver ```ztps```.

##Troubleshooting
###Gathering Diags
To gather a log file, just pre-pend ```PACKER_LOG=true PACKER_LOG_PATH=./debug.log```.  For example, ```PACKER_LOG=true PACKER_LOG_PATH=./debug.log packer build ztps-fedora_20_x86_64.json```.

###Potential Issues
####Error Detecting Host IP
Make sure that VMWare is running and that vmnet8 is enabled.  You can confirm this by going to your VMWare Fusion tools path, possibly ```/Applications/VMware Fusion.app/Contents/Library``` and typing ```sudo ./vmnet-cli --status```.

####Anaconda Installer Hangs at 'Installing Bootloader'
Type ```ctrl-c``` to exit the packer build, delete any references to the VM in the VMWare Fusion Library and then restart VMWare.

####References
http://www.packer.io/docs/builders/vmware-iso.html
