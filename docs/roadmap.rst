Roadmap
=======

The authoritative state, including the intended release, for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.   The information provided here is current at the time of publishing but is subject to change.   Please refer to the latest information in GitHub issues by filtering on the desired `milestone <https://github.com/arista-eosplus/ztpserver/milestones>`_.

Release 1.2
-----------

Target: November 2014

Enhancements
^^^^^^^^^^^^

* Add extra logging to "copy_file" action (`187 <https://github.com/arista-eosplus/ztpserver/pull/187>`_)
* Local interface in pattern specification should also allow ManagementXXX (`185 <https://github.com/arista-eosplus/ztpserver/pull/185>`_)
* Bootstrap script should cleanup on failure (`176 <https://github.com/arista-eosplus/ztpserver/pull/176>`_)
* utils.py: expand_range needs to be improved (`173 <https://github.com/arista-eosplus/ztpserver/pull/173>`_)
* Allow posting the startup-config to a node's folder, even if no startup-config is present (`169 <https://github.com/arista-eosplus/ztpserver/pull/169>`_)
* test_controller.py should cover both serialnumber and systemmac as identifiers (`168 <https://github.com/arista-eosplus/ztpserver/pull/168>`_)
* Tests for resource pool allocation (`161 <https://github.com/arista-eosplus/ztpserver/pull/161>`_)
* Bootstrap XMPP logging - client fails to create the specified MUC room (`148 <https://github.com/arista-eosplus/ztpserver/pull/148>`_)
* add_mlag_config action (action to arbitrate between MLAG peers)    (`141 <https://github.com/arista-eosplus/ztpserver/pull/141>`_)
* ZTPS server fails to write .node because lack of permissions (`126 <https://github.com/arista-eosplus/ztpserver/pull/126>`_)
* Location-based ZTR (`103 <https://github.com/arista-eosplus/ztpserver/pull/103>`_)
* Remove definition line from auto-generated pattern (`102 <https://github.com/arista-eosplus/ztpserver/pull/102>`_)
* tests for attribute tiebreakers for all 4 types of attributes (`101 <https://github.com/arista-eosplus/ztpserver/pull/101>`_)
* Breadth tests for resource pools (`94 <https://github.com/arista-eosplus/ztpserver/pull/94>`_)
* We need visibility into which files the server is loading and when (`52 <https://github.com/arista-eosplus/ztpserver/pull/52>`_)

Release 1.3
-----------

Target: January 2015

Enhancements
^^^^^^^^^^^^

* All requests from the client should contain the unique identifier of the node (`188 <https://github.com/arista-eosplus/ztpserver/pull/188>`_)
* make install_extension action dual-sup compatible (`180 <https://github.com/arista-eosplus/ztpserver/pull/180>`_)
* make install_cli_plugin action dual-sup compatible (`179 <https://github.com/arista-eosplus/ztpserver/pull/179>`_)
* make copy_file action dual-sup compatible (`178 <https://github.com/arista-eosplus/ztpserver/pull/178>`_)
* New command line option for ZTP Server which clears the resource pool allocations (`163 <https://github.com/arista-eosplus/ztpserver/pull/163>`_)
* Hook to run script after posting files on the server (`132 <https://github.com/arista-eosplus/ztpserver/pull/132>`_)
* Plugin infrastructure for resource pool allocation (`121 <https://github.com/arista-eosplus/ztpserver/pull/121>`_)
* Enhance actions to check md5sum of downloaded resources (`107 <https://github.com/arista-eosplus/ztpserver/pull/107>`_)
* V1 (`181 <https://github.com/arista-eosplus/ztpserver/pull/126>`_)

