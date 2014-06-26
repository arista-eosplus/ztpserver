#ZTPServer Setup - Packer.io VM Automation

##Introduction
You can use Packer.io to automate the creation of the ZTPServer VM.
By using this method, you can be sure that all of the required packages and dependencies are installed right out of the gate.

You can also use Packer to automate the setup of vEOS nodes.  This process is currently only supported for VMware.

###What's Supported
Currently, there is support for:

* **ZTPServer**
  * Ubuntu 12.04 on Virtual Box
  * Ubuntu 12.04 on VMWare
  * Fedora 20 on VMWare
  * Fedora 20 on Virtual Box
* **vEOS**
  * VMware

##Getting Started

 * [Fedora Installation Notes](https://github.com/arista-eosplus/ztpserver/tree/feature-packer/packer/Fedora)
 * [Ubuntu Installation Notes](https://github.com/arista-eosplus/ztpserver/tree/feature-packer/packer/Ubuntu)
 * [vEOS (VMware) Installation Notes](https://github.com/arista-eosplus/ztpserver/tree/feature-packer/packer/vEOS/VMware)
