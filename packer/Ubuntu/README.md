#ZTPServer Setup - Packer.io VM Automation

##Introduction
You can use Packer.io to automate the creation of the ZTPServer VM.
By using this method, you can be sure that all of the required packages and dependencies are installed right out of the gate.  
This procedure will create an Ubuntu VM that runs ZTPServer.  Below, you can choose whether you would like to build the VM for VMWare or VirtualBox.
This procedure will:

* Create a VM with 7GB Hard Drive
* 2GB RAM
* Ubuntu Server 12.04 Standard Install
* Python 2.7.5 with PIP
* Hostname ztps.ztps-test.com
    * eth0 (NAT) VBox DHCP
    * eth1 (vboxnet2) Runs ZTPServer services
* UFW Firewall disabled.
* Users
    * root/eosplus and ztpsadmin/eosplus
* DHCP installed with Option 67 configured (eth1 only)
* BIND DNS server installed with zone ztps-test.com
    * wildcard forward rule to 8.8.8.8 for all other queries
    * SRV RR for im.ztps-test.com
* rsyslog-ng installed; Listening on UDP and TCP (port 514)
* XMPP server configured for im.ztps-test.com
    * XMPP admin user ztpsadmin, passwd eosplus
* Apache2 installed and configured for ZTPServer (mod_wsgi) running on port 8080
* ZTPServer installed (with sameple files to get you running)

##Installation of Packer
> **Note:** This installation procedure requires internet access.

Packer.io automates the creation of the Virtual Machine.  
Therefore, the first step is downloading and installing Packer.

1. Download the appropriate binaries - http://www.packer.io/downloads.html
2. Unzip and move to desired location eg ~/packer or /usr/local/share/ or /usr/local/bin/
3. Set ENV variable (or just put Packer somewhere the ```PATH``` is already pointing - ```echo $PATH```)
    * EG: in ~/.bash_login, add ```PATH=$PATH:/path/to/packer/files```
4. Run ```packer``` to make sure ```PATH``` is updated.

##Creating a VM for use with VirtualBox
> **Note:** The following procedure was tested using VirtualBox 4.3.12.

> **IMPORTANT:** Regarding VirtualBox networks. The default setup places eth1 on vboxnet2. This might not be created in your Virtual Box environment.  
Therefore, open Vbox and open the General Settings/Preferences menu. Click on the **Network** tab. Click on **Host-only Networks.**
Add or Modify vboxnet2.  Configure the IP Address for 172.16.130.1, the Netmask 255.255.255.0 and turn off the DHCP server.

1. Retrieve the EOS+ packer files here.
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
       - ztps-ubuntu-12.04.4_amd64.json
       - /http
           - preseed.cfg
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
4. At this point you must choose whether to build the VM using VMWare or VirtualBox.
    Run ```packer build --only=vmware-iso ztps-ubuntu-12.04.4_amd64.json``` for VMWare, or
    Run ```packer build --only=virtualbox-iso ztps-ubuntu-12.04.4_amd64.json``` for VirtualBox
    You will see (example for Vbox):
    ```
    phil:Ubuntu phil$ packer build --only=virtualbox-iso ztps-ubuntu-12.04.4_amd64.json
    virtualbox-iso output will be in this color.

    ==> virtualbox-iso: Downloading or copying Guest additions checksums
        virtualbox-iso: Downloading or copying: http://download.virtualbox.org/virtualbox/4.3.12/SHA256SUMS
    ==> virtualbox-iso: Downloading or copying Guest additions
        virtualbox-iso: Downloading or copying: http://download.virtualbox.org/virtualbox/4.3.12/VBoxGuestAdditions_4.3.12.iso
    ==> virtualbox-iso: Downloading or copying ISO
        virtualbox-iso: Downloading or copying: http://releases.ubuntu.com/12.04/ubuntu-12.04.4-server-amd64.iso
    ```
5. Once the ISO is downloaded, packer brings up a VBox/VMWare VM. The installation will proceed without any user input.
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
      ... (shell script output)
    ```
8. After some extensive apt-getting (<5minutes), you will see:
    ```
    ==> virtualbox-iso: Gracefully halting virtual machine...
    ==> virtualbox-iso: Preparing to export machine...
        virtualbox-iso: Deleting forwarded port mapping for SSH (host port 3213)
    ==> virtualbox-iso: Exporting virtual machine...
        virtualbox-iso: Executing: export ztps-ubuntu-12.04_amd64-2014-06-13T13:20:20Z --output output-virtualbox-iso/ztps-ubuntu-12.04_amd64-2014-06-13T13:20:20Z.ovf
    ==> virtualbox-iso: Unregistering and deleting virtual machine...
    Build 'virtualbox-iso' finished.

    ==> Builds finished. The artifacts of successful builds are:
    --> virtualbox-iso: VM files in directory: output-virtualbox-iso
    ```
9. You now have a full-featured ZTPServer.
10. Simply type ```ztps``` to start the ztpserver.

> **Note**: If you created the VM with VBox, you will have to navigate to the output folder and double-click on the .ovf file to import it into Virtual Box.

##Setting up a Quick Demo
As part of the installation above, sample files were copied from the ztpserver-demo repo and placed into the necessary locations ( /etc/ztpserver/ and /usr/share/ztpserver).  Follow the steps below to create a quick demo:

1. type ```cd /usr/share/ztpserver/nodes```.
2. copy the default spine config to a new node that has the MAC address of your local vEOS instance. ```mv 005056761aae <local spine MAC>```.
3. start ztpserver ```ztps```.

##Troubleshooting
###Gathering Diags
To gather a log file, just pre-pend ```PACKER_LOG=true PACKER_LOG_PATH=./debug.log```.  For example, ```PACKER_LOG=true PACKER_LOG_PATH=./debug.log packer build ztps-fedora_20_x86_64.json```.

###Potential Issues

####References
http://www.packer.io/docs/builders/virtualbox-iso.html
