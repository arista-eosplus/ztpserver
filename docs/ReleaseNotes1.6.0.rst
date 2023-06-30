Release 1.6.0
-------------

New Modules
^^^^^^^^^^^

Enhancements
^^^^^^^^^^^^

* Add Ansible action docs (`352 <https://github.com/arista-eosplus/ztpserver/pull/352>`_) [`jerearista <https://github.com/jerearista>`_]
* Update Bootstrap regex used to detect old EOS versions that do not support unix sockets (`354 <https://github.com/arista-eosplus/ztpserver/pull/354>`_) [`jerearista <https://github.com/jerearista>`_]
* Add Docker (`362 <https://github.com/arista-eosplus/ztpserver/pull/362>`_) [`jerearista <https://github.com/jerearista>`_]
* Added support for streaming large EOS images to device for smaller switches (`376 <https://github.com/arista-eosplus/ztpserver/pull/376>`_) [`mhartista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fix RPM builds (`351 <https://github.com/arista-eosplus/ztpserver/pull/351>`_) [`jerearista <https://github.com/jerearista>`_]
* Do not add blank line at the start of a file (`355 <https://github.com/arista-eosplus/ztpserver/pull/355>`_) [`jerearista <https://github.com/jerearista>`_]
* Fix interface matcher for remote_interface to properly process regex() values (`360 <https://github.com/arista-eosplus/ztpserver/pull/360>`_) [`jerearista <https://github.com/jerearista>`_]
* Fix intf pattern range (`361 <https://github.com/arista-eosplus/ztpserver/pull/361>`_) [`jerearista <https://github.com/jerearista>`_]

Known Caveats
^^^^^^^^^^^^^
