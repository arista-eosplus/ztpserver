.. ZTPServer documentation master file, created by
   sphinx-quickstart on Tue Feb 18 16:40:25 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ZTPServer Overview
========================

ZTPServer provides a bootstrap environment for Arista EOS based products. It is written mostly in Python and leverages standard protocols like DHCP (for boot functions), HTTP (for bi-directional transport), XMPP and syslog (for logging). Most of the configuration files are YAML based.

This open source project is maintained by the `Arista Networks <http://arista.com/>`_ EOS+ services organization.

Highlights
``````````

* Extends the basic capability of EOS's zero-touch provisioning feature in order to allow more robust provisioning activities
* Is extensible, for easy integration into various network environments
* Can be run natively in EOS or any Linux server
* Arista EOS+ led community open source project

Features
````````

* Dynamic startup-config generation and automatic install
* Image and file system validation and standardization
* Connectivity validation and topology based auto-provisioning
* Config and device templates with dynamic resource allocation
* Zero-touch replacement and upgrade capabilities
* User extensible actions
* Email, XMPP, syslog based 

.. _an_introduction:

.. toctree::
   :maxdepth: 1

   overview
   install
   startup
   config
   examples
   tips
   internals
   glossary
   resources
   support
   ReleaseNotes
   caveats
   roadmap
   license

