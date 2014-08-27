
[![Build Status](https://travis-ci.org/arista-eosplus/ztpserver.png)](https://travis-ci.org/arista-eosplus/ztpserver)

Quick Overview
=====================
ZTPServer provides a bootstrap environment for Arista EOS based products.  ZTPserver interacts with the  ZeroTouch Provisioning (ZTP) mode of Arista EOS. The default ZTP start up mode triggers an unprovisioned Arista EOS nodes to enter a bootstrap readdy state if a valid configuration file is not already present on the internal flash storage.

ZTPServer provides a number of configurable bootstrap operation workflows that extend beyond simply loading an configuration and boot image. It provides the ability to define the target node through the introduction of definitions and templates that call pre-built actions and statically defined or dynamically generated attributes. The attributes and actions can also be extended to provide custom functionality that are specific to a given implementation. ZTPServer also provides a topology validation engine with a simple syntax to express LLDP neighbor adjacencies. It is written mostly in Python and leverages standard protocols like DHCP and DHCP options for boot functions, HTTP for bi-directional transport, and XMPP and syslog for logging. Most of the files that the user interacts with are YAML based.

ZTPServer Features
==================
* Automated configuration file generation and application
* Image and file system validation and standardization
* Connectivity validation and topology based auto-provisioning
* Config and device templates with resource allocation for dynamic deployments
* Zero touch replacement and upgrade capabilities
* User extensible actions
* Email, XMPP, syslog based logging and accounting of all processes

Docs
====
[ZTPServer official documentation](http://ztpserver.readthedocs.org/) is built and hosted at (http://ReadTheDocs.org/).

Contributing
============
Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for additional information.

Support
=======

* [Mailing List](https://groups.google.com/forum/#!forum/eosplus)
* eosplus-dev@arista.com
* IRC: irc.freenode.net#arista

Dependencies
============

Server
======
* [Python 2.7](https://www.python.org/download/releases/2.7/)
* [routes 2.0 or later](https://pypi.python.org/pypi/Routes)
* [webob 1.3 or later](http://webob.org/)
* [PyYaml 3.0 or later](http://pyyaml.org/)

Client
======
* Arista EOS 4.12.0 or later

License
=======
BSD-3, See LICENSE file
