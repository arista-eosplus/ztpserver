Caveats
=======

.. contents:: Topics

* Currently we do not support the use of management interfaces as a valid local interface names in neighbordb. When creating patterns, use ``any`` instead.

* Only a single entry in a resource pool may be allocated to a node.

* If using current versions of Fedora, firewalld is enabled by default and will block port 8080. isable firewalld via: ``bash-3.2$ chkconfig firewalld off``

