Support
=======


Contact
~~~~~~~

ZTPServer is an Arista-led open source community project.  Users and developers are encouraged to contribute to the project.  See `CONTRIBUTING <https://github.com/arista-eosplus/ztpserver/blob/develop/CONTRIBUTING.md>`_ for more details.

Community-based support is available through:

* `eosplus forum <https://groups.google.com/forum/#!forum/eosplus>`_
* eosplus-dev@arista.com.
* IRC: irc.freenode.net#arista

Commercial support, customization, and integration services are available through the EOS+ team at `Arista Networks, Inc <http://arista.com/>`_.  Contact eosplus-dev@arista.com for details.


Known caveats
~~~~~~~~~~~~~

.. contents:: :local:

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

*  v1.1: The management interfaces may not be used as valid local interface names in neighbordb. When creating patterns, use ``any`` instead.  (fixed in v1.2)

* Only a single entry in a resource pool may be allocated to a node.

* Users MUST be aware of the required EOS version for various hardware components (including transcievers).  Neighbor (LLDP) validation may fail if a node boots with an EOS version that does not support the installed hardware.  Moreoever, some EOS features configured via ZTPServer might be unsupported.   Please refer to the Release Notes for more compatability information and to the `Transceiver Guide <http://www.arista.com/assets/data/pdf/Transceiver-Guide.pdf>`_ .



Releases
~~~~~~~~

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

.. toctree::
    :maxdepth: 2
    :titlesonly:

    roadmap
    ReleaseNotes1.2
    ReleaseNotes1.1


Other Resources
~~~~~~~~~~~~~~~

ZTPServer documentation and other reference materials are below:

    * `GitHub ZTPServer Repository <https://github.com/arista-eosplus/ztpserver>`_
    * ZTPServer `wiki <https://github.com/arista-eosplus/ztpserver/wiki>`_
    * `Packer VM <https://github.com/arista-eosplus/packer-ztpserver>`_ build process.
    * `ZTPServer <https://pypi.python.org/pypi/ztpserver>`_ Python (PyPI) package.
    * `YAML Code Validator <http://yamllint.com/>`_
    

A quick video tutorial can be found here: http://www.youtube.com/playlist?list=PL6kEnPnH7OA4oc5jzhUW0ivVX1sMdfNpV
