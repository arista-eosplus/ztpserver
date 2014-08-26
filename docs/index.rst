.. ZTPServer documentation master file, created by
   sphinx-quickstart on Tue Feb 18 16:40:25 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ZTPServer Documentation
========================

ZTPServer provides a bootstrap environment for Arista EOS based products. It is written mostly in Python and leverages standard protocols like DHCP and DHCP options for boot functions, HTTP for bi-directional transport, and XMPP and syslog for logging. Most of the files that the user interacts with are YAML based.

This open source project is maintained by the `Arista Networks <http://arista.com/>`_ EOS+ services organization.

ZTPServer Highlights
````````````````````

* Extends the basic capability of EOS ZTP to allow more robust provisioning activities
* Extensible for easy integration into network operational environment
* Can be run natively in EOS
* An Arista EOS+ led community open source project

ZTPServer Features
``````````````````

* Automated configuration file generation and application
* Image and file system validation and standardization
* Connectivity validation and topology based auto-provisioning
* Config and device templates with resource allocation for dynamic deployments
* Zero touch replacement and upgrade capabilities
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

