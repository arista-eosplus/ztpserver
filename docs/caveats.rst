Known Caveats
==============

.. contents:: :local:

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

* Currently, the management interfaces may not be used as valid local interface names in neighbordb. When creating patterns, use ``any`` instead.

* Only a single entry in a resource pool may be allocated to a node.

* Be sure your host firewall allows incoming connections to ZTPServer.  The standalone server runs on port TCP/8080 by default.
  For **firewalld**: 

  * Open TCP/<port> through firewalld
    ``bash-3.2$ firewall-cmd --zone=public --add-port=<port>/tcp [--permanent]``
  * Stop firewalld
    ``bash-3.2$ systemctl status firewalld``
  * Disable firewalld
    ``bash-3.2$ systemctl disable firewalld``

