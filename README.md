# README for ZTP Server
This is the README for an implementation of a server to provide ZeroTouch Provisioning features to Arista EOS nodes. The default ZTP mode allows unprovisioned Arista EOS nodes to bootstrap themselves if a valid configuration file is not already present on the internal flash storage.

ZTPServer provides a number of configurable features that extend beyond simply loading an initial configuration and boot image. It provides the ability to define the target network element through the introduction of definitions and templates that call pre-built actions and statically defined or dynamically generated attributes. The attributes and actions can also be extended to provide custom actions that are specific to a given implementation. ZTPServer also provides a topology validation engine with a simple syntax to express LLDP neighbor adjacencies.


| Branch | Build Status |
|--------|--------------|
| develop | [![Build Status](https://travis-ci.org/arista-eosplus/ztpserver.png?branch=develop)](https://travis-ci.org/arista-eosplus/ztpserver)


##ZTPServer Features
* Automated configuration file generation and application
* Image and file system validation and standardization
* Connectivity validation and topology based auto-provisioning
* Config and device templates with resource allocation for dynamic deployments
* Zero touch replacement and upgrade capabilities
* User extensible actions
* Email, XMPP, syslog based logging and accounting of all processes

##Docs
https://github.com/arista-eosplus/ztpserver/wiki

## Support

* [Mailing List](https://groups.google.com/forum/#!forum/eosplus)
* eosplus@aristanetworks.com
* IRC: irc.freenode.net#arista

## Dependencies

### Server
* Python 2.7
* [routes 2.0 or later](https://pypi.python.org/pypi/Routes)
* [webob 1.3 or later](http://webob.org/)
* [PyYaml 3.0 or later](http://pyyaml.org/)

### Client
* Arista EOS 4.13.3 or later

## License
BSD-3, See LICENSE file

