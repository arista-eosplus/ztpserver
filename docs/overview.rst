ZTPServer Overview
==================

ZTPServer provides a robust server which enables comprehensive bootstrap solutions for Arista EOS based network elements.  ZTPserver interacts with the ZeroTouch Provisioning (ZTP) mode of EOS which takes an unprovisioned network element to a bootstrap ready state whenever a valid configuration file is not present on the internal flash storage.

ZTPServer provides a number of features that extend beyond simply loading a configuration file and and boot image on a node, including: 

* sending an advanced bootstrap client to the node: the bootstrap script.
* mapping each node to an individual definition which describes the bootstrap steps specific to that node
* defining configuration templates and actions which can be shared by multiple nodes - the actions can be customised using statically defined or dynamically generated attributes
* implementing environment-specific actions which integrate with external systems
* topology validation using a simple syntax to express LLDP neighbor adjacencies

ZTPServer is written in Python and leverages standard protocols like DHCP  (DHCP options for boot functions), HTTP(S) (for bi-directional transport), XMPP and syslog (for logging). Most of the configuration files are YAML based. 

**ZTPServer Highlights:**

* Extends the basic capability of EOS ZTP to allow more robust provisioning activities
* Extensible for easy integration into network operational environment
* Can be run natively in EOS or on a separate server.
* An Arista EOS+ led community open source project

**ZTPServer Features:**

* Automated configuration file generation and application
* Image and file system validation and standardization
* Connectivity validation and topology based auto-provisioning
* Configuration and device templates with resource allocation for dynamic deployments
* Zero Touch Replacement and upgrade capabilities
* User extensible actions
* Email, XMPP, syslog based logging and accounting of all processes

ZTPServer architecture
``````````````````````

There are 2 primary components of the ZTPServer implementation: 

* the **server** or ZTPS instance **AND**
* the **client** or bootstrap (a process running on each node, which connects to the server in order to provision the node)

Server
``````


.. image:: _static/Components.png
   :width: 353px
   :align: right

The server can run on any standard x86 server. Currently the only OS-es tested are Linux and MacOS, but theoretically any system that supports Python could run ZTPServer. The server provides a Python WSGI compliant interface, along with a standalone HTTP server. The built in HTTP server runs on port 8080 by default and provides bidirectional file transport for the bootstrap process.

The primary methods of provisioning a node are:

* **statically** via predefined node entries OR
* **dynamically**  generated via definitions and resource pools

Both methods can leverage topology validation via neighbordb and/or pattern entries. 

The definition associated with each node contains a set of actions that can perform a variety of functions that ultimately lead to a final device configuration and file structure. Actions can use statically configured attributes or leverage configuration templates and dynamically allocated attributes to generate the system configuration. Definitions, actions, attributes, templates, and resources are all defined in YAML files. 

Client
``````

.. image:: _static/AttrsActions.png
   :width: 353px
   :align: right

The client or **bootstrap file** is retrieved by the node via an HTTP GET request made to the ZTPServer (the URL of the file is retrieved via DHCP option 67). This file executes locally and gathers system and LLDP neighbor information from the unprovisioned device and returns it to the ZTPServer. Once the ZTPServer processes the information and confirms that it can provision the node, the client makes a request to the server for a definition file - this file will contain the list of all actions which need to be executed by the node in order to provision itself.

Throughout the provisioning process the bootstrap client can log via both local and remote logging and XMPP.

.. _message_flows:

ZTP Client-Server Message Flows
```````````````````````````````

A high level view of the client - server message flows can be seen in the following diagram:

.. image:: _static/ztpserver-seqdiag.png
   :alt: Message Flow Diagram


Topology Validation 
```````````````````

.. image:: _static/LeafDefn.png
   :width: 353px
   :align: right

ZTPServer provides a powerful topology validation engine via ``neighbordb`` or pattern files.  As part of the bootstrap process for each node, the LLDP information received on all ports is passed to the ZTPServer and pattern matched against either ``neighbordb`` or a node-specific pattern file (if a node is already configured on the server). Both are YAML files that are use a simple format to express strongly and loosely typed topology patterns. Pattern entries are processed top down and can include local or globally-defined variables (including regular expressions). 

Patterns in ``neighbordb`` match nodes to definitions (dynamic mode), while node-specific pattern files are used for cabling and connectivity validation (static mode).

Topology-validation can be disabled:

* globally (``disable_topology_validation=true`` in the server’s global configuration file) OR
* on a per-node basis, by adding a pattern which matches any topology

Operational modes
`````````````````

There are 4 operational modes for ZTPServer, explained below.  See :doc:`config_examples` to see how to use them.

Statically defined node without topology validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Node is created in /nodes before bootstrap
* Definition or startup-config is placed in /nodes
* Topology validation is disabled globally or with an open pattern

Statically defined node with topology validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Node is created in /nodes before bootstrap
* Definition or startup-config is placed in /nodes
* Topology validation is enabled globally and pattern is placed in /nodes

Strongly-typed node with topology validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Definition is node specific
* Node is dynamically created 
* Topology validation is enabled globally and pattern is placed in “/nodes/<system> or mapped to node MAC in neighbordb

Weakly-typed node with topology validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Definition is NOT node specific, leverages resources and templates
* Node is dynamically created 
* Topology validation is enabled globally and pattern is matched in neighbordb


