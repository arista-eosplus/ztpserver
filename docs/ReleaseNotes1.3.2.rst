Release 1.3.2
-------------

(Published March, 2015)

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

Bug fixes
^^^^^^^^^

* Prevented .node file from becoming corrupted on the server (`298 <https://github.com/arista-eosplus/ztpserver/issues/298>`_)
    .. comment
* Added .node filename to server-side logs (`297 <https://github.com/arista-eosplus/ztpserver/issues/297>`_)
    .. comment
* Change ``refresh_ztps`` script default to "master"
    Refresh_ztps will, by default, update the installation to the latest released version.   Previously, the default was to the development branch which may still be accomplished with ``refresh_ztps --branch develop``.
* Fixes to RPM packaging:

    - Quieted chcon during install (`295 <https://github.com/arista-eosplus/    ztpserver/issues/295>`_)
        .. comment
    - Fixed issue where config files may not be kept during upgrade (`296 <https://github.com/arista-eosplus/    ztpserver/issues/296>`_)
        .. comment
    - Fixed issue with native rpmbuild due to changes in handling VERSION (`294 <https://github.com/arista-eosplus/    ztpserver/issues/294>`_)
        .. comment

* Documentation updates:

    - Troubleshooting chapter  (`272 <https://github.com/arista-eosplus/    ztpserver/issues/272>`_)
        .. comment
    - Additional content in the ZTP Server Cookbook  (`289 <https://github.com/arista-eosplus/    ztpserver/issues/289>`_)
        .. comment
    - ZTP Server benchmarking results
        .. comment

