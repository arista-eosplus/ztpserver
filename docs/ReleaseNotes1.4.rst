Release 1.4
-----------

(Published August, 2015)

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

Enhancements
^^^^^^^^^^^^

* Plugin infrastructure for resource pool allocation (`121 <https://github.com/arista-eosplus/ztpserver/issues/121>`_)

* Use the order of entries in the file for allocating resources from a file via the ``allocate`` plugin (`319 <https://github.com/arista-eosplus/ztpserver/issues/319>`_)

* Documenatation updates:

    - Plugin infrastructure for resource pool allocation (`121 <https://github.com/arista-eosplus/ztpserver/issues/121>`_)

Bug fixes
^^^^^^^^^

* Starting ZTPServer fails because ``pkg_resources.DistributionNotFound: mock`` (`318 <https://github.com/arista-eosplus/ztpserver/issues/318>`_)

* Bootstrap file cannot be read by server (`308 <https://github.com/arista-eosplus/ztpserver/issues/308>`_)

* Bootstrap script fails because of broken pipe in EOS-4.14.5+ (`312 <https://github.com/arista-eosplus/ztpserver/issues/312>`_)
