Support
=======

.. contents:: :local:

Contact
~~~~~~~

ZTPServer is an Arista-led open source community project.  Users and developers are encouraged to contribute to the project.  See `CONTRIBUTING <https://github.com/arista-eosplus/ztpserver/blob/develop/CONTRIBUTING.md>`_ for more details.

Before requesting support, please collect the necessary data to include.   See :ref:`before-requesting-support`.

Commercial support may be purchased through your Arista account team.

Community-based support is available through:

* `eosplus forum <https://groups.google.com/forum/#!forum/eosplus>`_
* eosplus-dev@arista.com.
* IRC: irc.freenode.net#arista

Customization, and integration services are available through the EOS+ Consulting Services team at `Arista Networks, Inc <http://arista.com/>`_.  Contact eosplus-dev@arista.com or your account team for details.

Known caveats
~~~~~~~~~~~~~

.. contents:: :local:

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

* Only a single entry in a file-based resource pool may be allocated to a node (using the ``allocate(resource_pool`` plugin)).

* Users MUST be aware of the required EOS version for various hardware components (including transcievers).  Neighbor (LLDP) validation may fail if a node boots with an EOS version that does not support the installed hardware.  Moreoever, some EOS features configured via ZTPServer might be unsupported.   Please refer to the Release Notes for more compatability information and to the `Transceiver Guide <http://www.arista.com/assets/data/pdf/Transceiver-Guide.pdf>`_ .

*  If a lot of nodes are being booted at the same time and they all share the same file-based resource files (using the ``allocate(resource_pool`` plugin)), retrieving the definition for each might be slow (5s or longer) if the resource files are very large. The workaround is to use another plugin or custom actions and allocate the resources from alternative sources (other than shared files) - e.g. SQL

Releases
~~~~~~~~

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

.. toctree::
    :maxdepth: 2
    :titlesonly:

    ReleaseNotes2.0.0
    ReleaseNotes1.6.0
    ReleaseNotes1.5.0
    ReleaseNotes1.4.1
    ReleaseNotes1.4
    ReleaseNotes1.3.2
    ReleaseNotes1.3.1
    ReleaseNotes1.3
    ReleaseNotes1.2
    ReleaseNotes1.1


Roadmap highlights
~~~~~~~~~~~~~~~~~~

The authoritative state, including the intended release, for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.   The information provided here is current at the time of publishing but is subject to change.   Please refer to the latest information in GitHub issues by filtering on the desired `milestone <https://github.com/arista-eosplus/ztpserver/milestones>`_.

Release 1.5
-----------

Target: January 2016

* topology-based ZTR (`103 <https://github.com/arista-eosplus/ztpserver/pull/103>`_)
* ZTPServer Cookbook - advanced topics (`289 <https://github.com/arista-eosplus/ztpserver/pull/289>`_)
* benchmark scale tests (`261 <https://github.com/arista-eosplus/ztpserver/pull/261>`_)

Release 2.0
-----------

Target: March 2016

* configure HTTP timeout in bootstrap.conf (`246 <https://github.com/arista-eosplus/ztpserver/pull/246>`_)
* all requests from the client should contain the unique identifier of the node (`188 <https://github.com/arista-eosplus/ztpserver/pull/188>`_)
* dual-sup support for install_extension action (`180 <https://github.com/arista-eosplus/ztpserver/pull/180>`_)
* dual-sup support for  install_cli_plugin action (`179 <https://github.com/arista-eosplus/ztpserver/pull/179>`_)
* dual-sup support for  copy_file action (`178 <https://github.com/arista-eosplus/ztpserver/pull/178>`_)
* action for arbitrating between MLAG peers (`141 <https://github.com/arista-eosplus/ztpserver/pull/141>`_)
* plugin infrastructure for resource pool allocation (`121 <https://github.com/arista-eosplus/ztpserver/pull/121>`_)
* md5sum checks for all downloaded resources (`107 <https://github.com/arista-eosplus/ztpserver/pull/107>`_)
* topology-based ZTR (`103 <https://github.com/arista-eosplus/ztpserver/pull/103>`_)


Tutorial
~~~~~~~~~~~~~~

See https://eos.arista.com/quick-and-easy-veos-lab-setup/.


Other Resources
~~~~~~~~~~~~~~~

ZTPServer documentation and other reference materials are below:

    * `GitHub ZTPServer Repository <https://github.com/arista-eosplus/ztpserver>`_
    * ZTPServer `wiki <https://github.com/arista-eosplus/ztpserver/wiki>`_
    * `Packer VM <https://github.com/arista-eosplus/packer-ztpserver>`_ build process
    * `ZTPServer <https://pypi.python.org/pypi/ztpserver>`_ Python (PyPI) package
    * `YAML Code Validator <http://yamllint.com/>`_
    * `ZTPServer WSGI Benchmarking <https://eos.arista.com/ztpserver-benchmarking-the-webserver-gateway-interface>`_
