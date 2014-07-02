#vEOS Setup - Packer.io Automation
##Introduction
It can be time-consuming to get all of the vEOS VMs up, running and configured.
Here is a way to automate that procedure so that you can start testing ZTPServer even faster.

The following procedure will create three vEOS nodes,
and setup the virtual networks as depicted in the diagram below.

![vEOS Networks](https://raw.githubusercontent.com/arista-eosplus/ztpserver/feature-packer/tree/gh-pages/images/vEOS-spine-leaf.jpg)

###Prerequisites

 * **Packer** - If you do not have packer installed, follow the directions below:
    1. Download the appropriate binaries - http://www.packer.io/downloads.html
    2. Unzip and move to desired location eg ~/packer or /usr/local/share/ or /usr/local/bin/
    3. Set ENV variable (or just put Packer somewhere the ```PATH``` is already pointing - ```echo $PATH```)
        * EG: in ~/.bash_login, add ```PATH=$PATH:/path/to/packer/files```
    4. Run ```packer``` to make sure ```PATH``` is updated.
 * **vEOS Packer Plug-in**
    1. Download the custom [builder-vmware-veos](https://www.dropbox.com/s/7w57dyai1qgdd82/builder-vmware-veos) plug-in.
    2. Put this plug-in with all of the standard Packer executables.
    3. Modify the ```.packerconfig``` file to add this plug-in.  If this file does not exist, create it in ```$HOME/.packerconfig``` (this is a location Packer will look for it). Add the following config to that file:
    ```
    {
        "builders": {
          "vmware-veos": "builder-vmware-veos"
        }
    }
    ```
 * You will need to log into your Arista.com account to obtain the following files from https://www.arista.com/en/support/software-download:
     * Aboot-veos-2.0.8.iso
     * vEOS-4.13.5F.vmdk
 * **Virtual Networks**
     If you have not configured the vmnets described in the diagram above, you can run ```setup-fusion.sh``` to do this for you.  You can modify the script to only modify/create certain vmnets.
     EG ```VMNETS=(2 3 4 5 6 7 9 10 11)```

##Creating vEOS Nodes for VMWare
1. ```cd``` to the ```vEOS/VMware``` directory.
2. Place the files mentioned above into the correct directories. Your directory should look like:

    ```
    vEOS
       /VMware
          - vEOS.json
          /source
              - vEOS.vmx
              - vEOS-4.13.5F.vmdk
              - Aboot-veos-2.0.8.iso
    ```
3. The vEOS.json file contains unique configuration for three vEOS nodes - vEOS-1/2/3 as depicted above.
    * It requires a non-trivial amount of CPU/memory to turn up all three at the same time.  If you're feeling daring, run:
        * ```packer build vEOS.json```
    * If you'd like to build the nodes one at a time, run:
        * ```packer build --only=vEOS1 vEOS.json```
        * ```packer build --only=vEOS2 vEOS.json```
        * ```packer build --only=vEOS3 vEOS.json```
