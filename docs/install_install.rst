Installation
============

.. contents:: Topics


Requirements
`````````````

Examples in this guide are based on the following:

 * python 2.7
 * dhcp server - (dhcpd)
 * pip
 * git

.. NOTE:: We recommend using a Linux distribution which has Python 2.7 as its standard Python install (e.g. yum in Centos requires Python 2.6 and a dual Python install can be fairly tricky and buggy). This guide was written based ZTPServer v1.0.0 installed on Fedora 20. 


Turn-key VM Creation
````````````````````

The turn-key VM option leverages `Packer <http://www.packer.io/>`_ to auto generate a VM on your local system. Packer.io automates the creation of the ZTPServer VM. All of the required packages and dependencies are installed and configured. The current Packer configuration allows you to choose between VirtualBox or VMWare as your hypervisor and each can support Fedora 20 or Ubuntu Server 12.04.

VM Specification:

* 7GB Hard Drive
* 2GB RAM
* Hostname ztps.ztps-test.com

  * eth0 (NAT) DHCP
  * eth1 (hostonly) 172.16.130.10

* Firewalld/UFW disabled.
* Users

  * root/eosplus
  * ztpsadmin/eosplus
* Python 2.7.5 with PIP
* DHCP installed with Option 67 configured (eth1 only)
* BIND DNS server installed with zone ztps-test.com

  * wildcard forwarding rule passing all other queries to 8.8.8.8
  * SRV RR for im.ztps-test.com
* rsyslog-ng installed; Listening on UDP and TCP (port 514)
* ejabberd (XMPP server) configured for im.ztps-test.com

  * XMPP admin user ztpsadmin, passwd eosplus
* httpd installed and configured for ZTPServer (mod_wsgi) listening on port 8080
* ZTPServer installed
* ztpserver-demo repo files pre-loaded


See the Packer VM `code and documentation <https://github.com/arista-eosplus/packer-ztpserver>`_ as well as the `ZTPServer demo files <https://github.com/arista-eosplus/ztpserver-demo>`_ for the Packer VM.

PyPI Package (pip install)
``````````````````````````

ZTPServer may be installed as a PyPI package.

This option assumes you have a server with python and pip pre-installed.  See `installing pip <https://pip.pypa.io/en/latest/installing.html>`_.

Once pip is installed, type:

.. code-block:: console

    bash-3.2$ pip install ztpserver

The pip install process will install all dependencies and run the install script, leaving you with a ZTPServer instance ready to configure.

Manual installation
```````````````````

.. NOTE::: If using the Packer based VM image, all of these steps will have been completed, please reference the VM documentation.

Configure the DHCP Service
--------------------------

Set up your DHCP infrastructure to server the full path to the ZTPServer bootstrap file via option 67.  This can be performed on any DHCP server.  Instructions are provided, below, for ISC dhcpd.

Get dhcpd:

    RedHat:
        ``bash-3.2$ sudo yum install dhcp``

    Ubuntu:
        ``bash-3.2$ sudo apt-get install isc-dhcp-server``


If using dhcpd, the following example configuration will add a network (192.168.100.0/24) for servicing DHCP requests for ZTPServer::

    subnet 192.168.100.0 netmask 255.255.255.0 {
      range 192.168.100.200 192.168.100.205;
      option routers 192.168.100.1;
      option domain-name-servers <ipaddr>;
      option domain-name "<org>";
      option bootfile-name "http://<ztp_hostname_or_ip>:8080/bootstrap";
    }

Enable and start the dhcpd service.
-----------------------------------

RedHat (and derivative Linux implementations)
``bash-3.2# sudo /usr/bin/systemctl enable dhcpd.service``
``bash-3.2# sudo /usr/bin/systemctl start dhcpd.service``

Ubuntu (and derivative Linux implementations)
``bash-3.2# sudo /usr/sbin/service isc-dhcp-server start``
Check that /etc/init/isc-dhcp-server.conf is configured for automatic startup on boot.


Download and install ZTPServer
------------------------------

Once the above system requirements are met, use the following git command to pull the develop branch into a local directory on the server where you want to install ZTPServer:

.. code-block:: console

    bash-3.2$ git clone https://github.com/arista-eosplus/ztpserver.git -b develop

Then checkout the release desired:

.. code-block:: console

    bash-3.2$ cd ztpserver
    bash-3.2$ git checkout v1.0.0

Execute ``setup.py`` to build and then install ZTPServer

.. code-block:: console

    [root@localhost ztpserver]# python setup.py build
    running build
    running build_py
    ...
    
    [root@localhost ztpserver]# sudo python setup.py install
    running install
    running build
    running build_py
    running install_lib
    ...

Edit the global configuration file located at ``/etc/ztpserver/ztpserver.conf`` (if needed). See the :ref:`install_config` options for more information.

At a minimum, create the ``/usr/share/ztpserver/neighbordb`` file.

