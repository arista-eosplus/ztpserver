# README for ZTP Server
This is the README for an implementation of a server to provide ZeroTouch Provisioning features to Arista EOS nodes.  The ZTP mode allows Arista EOS nodes to initially bootstrap themselves if a valid configuration file is not already present on the internal flash drive.

This ZTP Server provides a number of configurable features that extend beyond simply loading an initial configuration.   The server provides the ability to define the target network element through the introduction of attributes and actions.   The attributes and actions can also be extended to provide custom actions that are specific to a given implementation.


| Branch | Build Status |
|--------|--------------|
| develop | [![Build Status](https://travis-ci.org/arista-eosplus/ztpserver.png?branch=develop)](https://travis-ci.org/arista-eosplus/ztpserver)

## Features

## Support

* [Mailing List](https://groups.google.com/forum/#!forum/eosplus)
* IRC: irc.freenode.net#arista

## Dependencies

### Server
* Python 2.7
* [routes 2.0 or later](https://pypi.python.org/pypi/Routes)
* [webob 1.3 or later](http://webob.org/)
* [PyYaml 3.0 or later](http://pyyaml.org/)

### Client
* Arista EOS 4.12 or later

## License
BSD-3, See LICENSE file

