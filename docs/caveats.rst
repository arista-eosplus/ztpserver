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

* Users MUST be aware of the required EOS version for various hardware components (including transcievers).  Neighbor (LLDP) validation may fail if a node boots with an EOS version that does not support the installed hardware.  Moreoever, some EOS features configured via ZTPServer might be unsupported.   Please refer to the Release Notes for more compatability information.
