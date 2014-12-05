Support
=======

.. contents:: :local:

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


Roadmap highlights
~~~~~~~~~~~~~~~~~~

The authoritative state, including the intended release, for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.   The information provided here is current at the time of publishing but is subject to change.   Please refer to the latest information in GitHub issues by filtering on the desired `milestone <https://github.com/arista-eosplus/ztpserver/milestones>`_.

Release 1.3
-----------

Target: January 2015

* validate all YAML files via 'ztpserver --validate' (`247 <https://github.com/arista-eosplus/ztpserver/pull/247>`_)
* action which enables running arbitrary set of EOS CLI commands (`211 <https://github.com/arista-eosplus/ztpserver/pull/211>`_)
* show server's version in startup logs (`207 <https://github.com/arista-eosplus/ztpserver/pull/207>`_)
* command-line option for clearing resource pools (`163 <https://github.com/arista-eosplus/ztpserver/pull/163>`_)
* hook to run script after posting files on the server (`132 <https://github.com/arista-eosplus/ztpserver/pull/132>`_)
* action which enables running arbitrary bash commands (`108 <https://github.com/arista-eosplus/ztpserver/pull/108>`_)


Release 2.0
-----------

Target: March 2015

* configure HTTP timeout in bootstrap.conf (`246 <https://github.com/arista-eosplus/ztpserver/pull/246>`_)
* all requests from the client should contain the unique identifier of the node (`188 <https://github.com/arista-eosplus/ztpserver/pull/188>`_)
* dual-sup support for install_extension action (`180 <https://github.com/arista-eosplus/ztpserver/pull/180>`_)
* dual-sup support for  install_cli_plugin action (`179 <https://github.com/arista-eosplus/ztpserver/pull/179>`_)
* dual-sup support for  copy_file action (`178 <https://github.com/arista-eosplus/ztpserver/pull/178>`_)
* action for arbitrating between MLAG peers (`141 <https://github.com/arista-eosplus/ztpserver/pull/141>`_)
* plugin infrastructure for resource pool allocation (`121 <https://github.com/arista-eosplus/ztpserver/pull/121>`_)
* md5sum checks for all downloaded resources (`107 <https://github.com/arista-eosplus/ztpserver/pull/107>`_)
* topology-based ZTR (`103 <https://github.com/arista-eosplus/ztpserver/pull/103>`_)


Video tutorial
~~~~~~~~~~~~~~

See http://www.youtube.com/playlist?list=PL6kEnPnH7OA4oc5jzhUW0ivVX1sMdfNpV.


Other Resources
~~~~~~~~~~~~~~~

ZTPServer documentation and other reference materials are below:

    * `GitHub ZTPServer Repository <https://github.com/arista-eosplus/ztpserver>`_
    * ZTPServer `wiki <https://github.com/arista-eosplus/ztpserver/wiki>`_
    * `Packer VM <https://github.com/arista-eosplus/packer-ztpserver>`_ build process
    * `ZTPServer <https://pypi.python.org/pypi/ztpserver>`_ Python (PyPI) package
    * `YAML Code Validator <http://yamllint.com/>`_
    
