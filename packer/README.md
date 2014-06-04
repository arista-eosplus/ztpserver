#ZTPServer Setup - Packer.io VM Automation

##Introduction
You can use Packer.io to automate the creation of the ZTPServer VM.  By using this method, you can be sure that all of the required packages and dependencies are installed right out of the gate.  This procedure will:

* Create a VM with 7GB Hard Drive
* 2GB RAM
* Fedora 19 Desktop with Gnome
* Hostname ztps.ztps-test.com
* Users
    * root/ztpserver and ztps/eosplus
* DHCP installed with Option 66/67 configured
* BIND DNS server installed with zone ztps-test.com
    * wildcard forward rule to 8.8.8.8 for all other queries
    * SRV RR for im.ztps-test.com
* rsyslog-ng installed
* XMPP server configured for im.ztps-test.com

##Installation of Packer
Packer.io automates the creation of the Virtual Machine.  Therefore, the first step is downloading and installing Packer.

1. Download the appropriate binaries - http://www.packer.io/downloads.html
2. Unzip and move to desired location eg ~/packer or /usr/local/share/ or /usr/local/bin/
3. Set ENV variable (or just put Packer somewhere the ```PATH``` is already pointing - ```echo $PATH```)
    * EG: in ~/.bash_login, add ```PATH=$PATH:/path/to/packer/files```
4. Run ```packer``` to make sure ```PATH``` is updated.

##Creating a VM for use with VMWare Fusion
The following procedure was tested using VMWare Fusion 6.0.3.

1. Retrieve the EOS+ packer files here: 
2. ```cd``` to the location of the .json
3. Run 

You will see:
```
phil:ztpserver phil$ packer build ztps-fedora_20_x86_64.json.testing
vmware-iso output will be in this color.

==> vmware-iso: Downloading or copying ISO
    vmware-iso: Downloading or copying: http://mirrors.xmission.com/fedora/linux/releases/20/Fedora/x86_64/iso/Fedora-20-x86_64-netinst.iso
==> vmware-iso: Creating virtual machine disk
==> vmware-iso: Building and writing VMX file
==> vmware-iso: Starting HTTP server on port 8360
==> vmware-iso: Starting virtual machine...
==> vmware-iso: Waiting 2s for boot...
==> vmware-iso: Connecting to VM via VNC
==> vmware-iso: Typing the boot command over VNC...
==> vmware-iso: Waiting for SSH to become available...
```

##The Minimal Fedora 20 ISO
Install net-insta iso, then
 - yum install net-tools
 - 

####References
http://www.packer.io/docs/builders/vmware-iso.html