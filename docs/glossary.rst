Glossary of Terms
=================

node
    a node is a EOS instance which is provisioned via ZTPServer. A node is uniquely identified by its system MAC address and/or unique position in the network.

action
    an action is a Python script which is executed during the bootstrap process.

attribute
    an attribute is a variable that holds a value. attributes are used in order to customise the behaviour of actions which are executed during the bootstrap process.

definition
    a definition is a YAML file that contains a collection of all actions (and associated attributes) which need to run during the bootstrap process in order to fully provision a node

pattern
    a pattern is a YAML file which describes a node in terms of its identity (system MAC) and/or location in the network (neighbors)

neighbordb
    neighbordb is a YAML file which contains a collection of patterns which can be used in order to map nodes to definitions

resource pool
    a resource pool is a YAML file which provides a mapping between a set or resources and the nodes to which some of the resources might have been allocated to. The nodes are uniquely identified via their system MAC.
