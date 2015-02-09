Release 1.3
-----------

(Published February, 2015)

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

Enhancements
^^^^^^^^^^^^

* ``ztps --validate`` validates:

  - neighbordb syntax and patterns
  - resource files syntax
  - definition files syntax
  - pattern files syntax

::

  $ ztps --validate
  Validating neighbordb ('/usr/share/ztpserver/neighbordb')...
  2015-01-13 18:03:55,006:ERROR:[validators:111] N/A: PatternValidator validation error: missing attribute: definition
  2015-01-13 18:03:55,006:ERROR:[validators:111] N/A: NeighbordbValidator validation error: invalid patterns: set([(0, 's7151')])

  ERROR: Failed to validate neighbordb patterns
  Invalid Patterns (count: 1)
  ---------------------------
  [0] s7151

  Validating definitions...
  Validating /usr/share/ztpserver/definitions/leaf.definition... Ok!
  Validating /usr/share/ztpserver/definitions/leaf-no_vars.definition... Ok!
  
  Validating resources...
  Validating /usr/share/ztpserver/resources/leaf_man_ip... Ok!
  Validating /usr/share/ztpserver/resources/leaf_spine_ip...
  ERROR: Failed to validate /usr/share/ztpserver/resources/leaf_spine_ip
  validator: unable to deserialize YAML data:
  10.0.0.51/24: null
  10.0.0.53/24: null
  dfdsf dsfsd
  10.0.0.54/24: JPE14140273
  
  Error:
  while scanning a simple key
  in "<string>", line 3, column 1:
  dfdsf dsfsd 
  could not found expected ':'
  in "<string>", line 5, column 1:
  10.0.0.54/24: JPE14140273
  ^

  Validating nodes...
  Validating /usr/share/ztpserver/nodes/JAS12170010/definition... Ok!
  Validating /usr/share/ztpserver/nodes/JAS12170010/pattern... Ok!

* *run_bash_script* action allows users to run bash scripts during the bootstrap process

* *run_cli_commands* action allows users to run CLI commands during the bootstrap process

* *config-handlers* can be used in order to trigger scripts on the server on PUT startup-config request completion

* The auto **replace_config** action which is added to the definition whenever a startup-config file is present in a node's folder is now the first action in the definition which is sent to the client. This enables performing configuration updates during ZTR (Zero Touch Replacement) via 'always_execute' *add_config* actions in the definition file. One particularly interesting use-case is replacing one node with another one of a different model.

* ``ztps --clear-resources`` clears all resource allocations

* server-side logs are timestamped by default

* ZTP Server shows running version on-startup

::

  # ztps
  2015-02-09 16:50:35,922:INFO:[app:121] Starting ZTPServer v1.3.0...
  ...


Bug fixes
^^^^^^^^^

* upgrades/downgrades to/from v1.3+ will preserve the configuration files

  - *ztpserver.conf*, *ztpserver.wsgi*, *bootstrap.conf* and *neighbordb* are preserved (new default files are installed under *<filename>*.new)
  - all definitions, config-handlers, files, node folder, resources and files are preserved
  - *bootstrap* file, actions and libraries are always overwritten

* *bootstrap.conf* now supports specifying empty config sections:

::

  logging:
    ...
  xmpp:

::

  logging:
  xmpp:
    ...

