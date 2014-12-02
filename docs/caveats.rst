Known Caveats
==============

.. contents:: :local:

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

*  v1.1: The management interfaces may not be used as valid local interface names in neighbordb. When creating patterns, use ``any`` instead.  (Fixed in v1.2)

* Only a single entry in a resource pool may be allocated to a node.

* Users MUST be aware of the required EOS version for various hardware components (including transcievers).  Neighbor (LLDP) validation may fail if a node boots with an EOS version that does not support the installed hardware.  Moreoever, some EOS features configured via ZTPServer might be unsupported.   Please refer to the Release Notes for more compatability information.
