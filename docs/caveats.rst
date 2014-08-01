Known Caveats
==============

.. contents:: Topics

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

* Currently, the management interfaces may not be used as valid local interface names in neighbordb. When creating patterns, use ``any`` instead.

* Only a single entry in a resource pool may be allocated to a node.

* Be sure your host firewall allows incoming connections to ZTPServer.  The standalone server runs on port TCP/8080.
  For **firewalld**: 
  * Open TCP/8080 through firewalld via: ``bash-3.2$ firewall-cmd --zone=public --add-port=8080/tcp [--permanent]``
  * Stop firewalld via: ``bash-3.2$ systemctl status firewalld``
  * Disable firewalld via: ``bash-3.2$ systemctl disable firewalld``

