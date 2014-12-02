Release 1.2
-----------

(Published December, 2014)

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

Enhancements
^^^^^^^^^^^^

* Enhance neighbordb documentation (`255 <https://github.com/arista-eosplus/ztpserver/issues/255>`_)
    .. comment
* In case of failure, bootstrap cleanup removes temporary files that were copied onto switch during provisioning (`253 <https://github.com/arista-eosplus/ztpserver/issues/253>`_)
    .. comment
* "ERROR: unable to disable COPP" should be a warning on old EOS platforms (`242 <https://github.com/arista-eosplus/ztpserver/issues/242>`_)
    A detailed warning will be displayed if disabling COPP fails (instead of an error).

* Enhance documentation for open patterns(`239 <https://github.com/arista-eosplus/ztpserver/issues/239>`_)
    .. comment
* Document guidelines on how to test ZTPS (`235 <https://github.com/arista-eosplus/ztpserver/issues/235>`_)
    .. comment
* Document http://www.yamllint.com/ as a great resource for checking YAML files syntax (`234 <https://github.com/arista-eosplus/ztpserver/issues/234>`_)
    .. comment
* Make ”name" an optional attribute in local pattern files (`233 <https://github.com/arista-eosplus/ztpserver/issues/233>`_)
    node pattern file can contain only the interfaces directive now
    e.g.
    ::

        interfaces:
        - any:
            device: any
            port: any

* Documentation should clarify that users must be aware of the EOS version in which certain transceivers were introduced (`232 <https://github.com/arista-eosplus/ztpserver/issues/232>`_)
    .. comment
* Enhance the Apache documentation (`231 <https://github.com/arista-eosplus/ztpserver/issues/231>`_)
    .. comment
* Enhance documentation related to config files (`229 <https://github.com/arista-eosplus/ztpserver/issues/229>`_)
    .. comment
* Disable meta information checks for remote URLs (`224 <https://github.com/arista-eosplus/ztpserver/issues/224>`_)

    - if URL points to ZTP server and destination is on flash, use metadata request to compute disk space (other metadata could be added here in the future)
    - it URL points to a remote server and destination is on flash, use 'content-length' to compute disk space - this will skip the metadata request

* Assume port 514 for remote syslog, if missing from bootstrap.conf (`218 <https://github.com/arista-eosplus/ztpserver/issues/218>`_)

    When configuring remote syslog destinations in bootstrap.conf, the port number is not mandatory anymore (if missing, a default value of 514 is assumed).

    e.g.
    ::

        logging:
          - destination: pcknapweed
            level: DEBUG

* Deal more gracefully with YAML errors in neighbordb (`216 <https://github.com/arista-eosplus/ztpserver/issues/216>`_)
    YAML serialization errors are now exposed in ZTPS logs:
    ::

        DEBUG: [controller:170] JPE14140273: running post_node
        ERROR: [topology:83] JPE14140273: failed to load file: /usr/share/ztpserver/neighbordb
        ERROR: [topology:116] JPE14140273: failed to load neighbordb:
        <b>expected a single document in the stream
          in "<string>", line 26, column 1:
            patterns:
            ^
        but found another document
          in "<string>", line 35, column 1:
            ---
            ^</b>
        DEBUG: [controller:182] JPE14140273: response to post_node: {'status': 400, 'body': '', 'content_type': 'text/html'}
        s7056.lab.local - - [03/Nov/2014 21:05:33] "POST /nodes HTTP/1.1" 400 0

* Deal more gracefully with DNS/connectivity errors while trying to access remote syslog servers (`215 <https://github.com/arista-eosplus/ztpserver/issues/215>`_)
    Logging errors (e.g. bogus destination) will not be automatically logged by the bootstrap script. In order to debug logging issues, simply uncomment the following lines in the bootstrap script: 
    ::

        #---------------------------------SYSLOG----------------------
        # Comment out this section in order to enable syslog debug
        # logging
        logging.raiseExceptions = False
        #---------------------------------XMPP------------------------

    Example of output which is suppressed by default:
    ::

        Traceback (most recent call last):
          File "/usr/lib/python2.7/logging/handlers.py", line 806, in emit
            self.socket.sendto(msg, self.address)
        gaierror: [Errno -2] Name or service not known
        Logged from file bootstrap, line 163

* Make ”name" an optional attribute in node definitions (`214 <https://github.com/arista-eosplus/ztpserver/issues/214>`_)
    Definitions under /nodes/<NODE> do not have to have a 'name' attribute.

* Increase HTTP timeout in bootstrap script (`212 <https://github.com/arista-eosplus/ztpserver/issues/212>`_)
    HTTP timeout in bootstrap script is now 30s. https://github.com/arista-eosplus/ztpserver/issues/246 tracks making that configurable via bootstrap.conf. In the meantime, the workaround for changing it is manually editing the bootstrap file.

* Remove fake prefixes from client and actions function names in docs (`204 <https://github.com/arista-eosplus/ztpserver/issues/204>`_)
    .. comment
* Tips and tricks - clarify vEOS version for both ways to set system MAC (`203 <https://github.com/arista-eosplus/ztpserver/issues/203>`_)
    .. comment

* Enhance logging for "copy_file" action (`187 <https://github.com/arista-eosplus/ztpserver/issues/187>`_)
* Local interface pattern specification should also allow management interfaces (`185 <https://github.com/arista-eosplus/ztpserver/issues/185>`_)
    Local interface allows for:

    - management interface or interface range, using either mXX, maXX, MXX, MaXX, ManagementXX (where XX is the range)
    - management + ethernet specification on the same line: Management1-3,Ethernet3,5,6/7

* Bootstrap script should cleanup on failure (`176 <https://github.com/arista-eosplus/ztpserver/issues/176>`_)
    ::

        $ python bootstrap --help
        usage: bootstrap [options]

        optional arguments:
          -h, --help            show this help message and exit
          --no-flash-factory-restore, -n
                                Do NOT restore flash config to factory defaul

    Added extra command-line option for the bootstrap script for testing.

    Default behaviour:
     - clear rc.eos, startup-config, boot-extensions (+folder) at the beginning of the process
     - in case of failure, delete all new files added to flash

    '-n' behaviour:
     - leave rc.eos, startup-config, boot-extensions (+folder) untouched
     - instead, bootstrap will create the new files corresponding to the above, with the ".ztp" suffix
     - never remove any files from flash at the end of the process, regardless of the outcome

* Allow posting the startup-config to a node's folder, even if no startup-config is already present (`169 <https://github.com/arista-eosplus/ztpserver/issues/169>`_)
    .. comment
* Remove definition line from auto-generated pattern (`102 <https://github.com/arista-eosplus/ztpserver/issues/102>`_)
    When writing the pattern file in the node's folder (after a neighbordb match):

     - 'definition' line is removed
     - 'variables' and 'node' are only written if non-empty
     - 'name' (that's the pattern's name) and 'interfaces' are always written


Fixed
^^^^^


* server_url requires trailing slash "/" when adding subdirectory (`244 <https://github.com/arista-eosplus/ztpserver/issues/244>`_)
    .. comment
* Error when doing static node provisioning using replace_config (`241 <https://github.com/arista-eosplus/ztpserver/issues/241>`_)
    .. comment
* XMPP messages are missing the system ID (`236 <https://github.com/arista-eosplus/ztpserver/issues/236>`_)
    XMPP messages now contain the serial number of the switch sending the message. 'N/A' is shown if the serial number is not available or empty.

* Fix "node:" directive behaviour in neighbordb (`230 <https://github.com/arista-eosplus/ztpserver/issues/230>`_)
    The following 'patterns' are now valid in neighbordb:
     - name, definition, node [,variables]
     - name, definition, interfaces [,variables]
     - name, definition, node, interfaces [,variables]

* node.retrieve_resource should be a no-op if the file is already on the disk (`225 <https://github.com/arista-eosplus/ztpserver/issues/225>`_)
    When computing the available disk space on flash for saving a file, the length of the file which is about to be overwritten is also considered.

* Ignore content-type when retrieving a resource from a remote server or improve on the error message (`222 <https://github.com/arista-eosplus/ztpserver/issues/222>`_)
    If a resource is retrieved from some other server (which is NOT the ZTPServer itself), then we allow any content-type.

* ztpserver.wsgi is not installed by setup.py (`220 <https://github.com/arista-eosplus/ztpserver/issues/220>`_)
    .. comment
* ztps --validate broken in 1.1 (`217 <https://github.com/arista-eosplus/ztpserver/issues/217>`_)
    ::

        ztps --validate PATH_TO_NEIGHBORDB

    can be used in order to validate the syntax of a neighbordb file.

* install_extension action copies the file to the switch but doesn't install it (`206 <https://github.com/arista-eosplus/ztpserver/issues/206>`_)
    .. comment
* Bootstrap XMPP logging - client fails to create the specified MUC room (`148 <https://github.com/arista-eosplus/ztpserver/issues/148>`_)
    In order for XMPP logging to work, a non-EOS user need to be connected to the room specified in bootstrap.conf, before the ZTP process starts. The room has to be created (by the non-EOS user), before the bootstrap client starts logging the ZTP process via XMPP.

* ZTPS server fails to write .node because lack of permissions (`126 <https://github.com/arista-eosplus/ztpserver/issues/126>`_)
    .. comment

