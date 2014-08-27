Release 1.1
-----------

(Published August, 2014)

The authoritative state for any known issue can be found in `GitHub issues <https://github.com/arista-eosplus/ztpserver/issues>`_.

Enhancements
^^^^^^^^^^^^

* V1.1.0 docs (`181 <https://github.com/arista-eosplus/ztpserver/pull/181>`_)
    Documentation has been completely restructured and is now hosted at http://ztpserver.readthedocs.org/.
* refresh_ztps - util script to refresh ZTP Server installation (`177 <https://github.com/arista-eosplus/ztpserver/issues/177>`_)
    /utils/refresh_ztps can be used in order to automatically refresh the installation of ZTP Server to the latest code on GitHub.  This can be useful in order to pull bug fixes or run the latest version of various development branches.                                      
* Et49 does not match Ethernet49 in neighbordb/pattern files (`172 <https://github.com/arista-eosplus/ztpserver/issues/172>`_)
    The local interface in an interface pattern does not have to use the long interface name. For example, all of the following will be treated similarly: Et1, e1, et1, eth1, Eth1, ethernet1, Ethernet1.

    Note that this does not apply to the remote interface, where different rules apply.
* Improve server-side log messages when there is no match for a node on the server (`171 <https://github.com/arista-eosplus/ztpserver/issues/171>`_)
    .. comment
* Improve error message on server side when definition is missing from the definitions folder (`170 <https://github.com/arista-eosplus/ztpserver/issues/170>`_)
    .. comment
* neighbordb should also support serialnumber as node ID (along with system MAC) (`167 <https://github.com/arista-eosplus/ztpserver/issues/167>`_)
    Server now supports two types of unique identifiers, as specified in ztpserver.conf:
    ::

        # UID used in the /nodes structure (either systemmac or serialnumber)
        identifier = serialnumber

    The configuration is global and applies to a single run of the server (neighbordb, resource files, nodes' folders, etc.).
* serialnumber should be the default identifier instead of systemmac (`166 <https://github.com/arista-eosplus/ztpserver/issues/166>`_)
    The default identifier in ztpserver.conf is the serial number. e.g.
    ::

        # UID used in the /nodes structure (either systemmac or serialnumber)
        identifier = serialnumber

    This is different from v1.0, where the systemmac was the default.
* Document which actions are dual-sup compatible and which are not (`165 <https://github.com/arista-eosplus/ztpserver/issues/165>`_)
    All actions now document whether they are dual-sup compatible or not. See documentation for the details.
* dual-sup support for install_image action (`164 <https://github.com/arista-eosplus/ztpserver/issues/164>`_)
    install_image is now compatible with dual-sup systems.
* Resource pool allocation should use the identifier instead of the systemmac (`162 <https://github.com/arista-eosplus/ztpserver/issues/162>`_)
    The values in the resource files will be treated as either system MACs or serial numbers, depending on what identifier is configured in the global configuration file.
* Document actions APIs (`157 <https://github.com/arista-eosplus/ztpserver/issues/157>`_)
    The API which can be used by actions is now documented in the documentation for the bootstrap script module.
* Get rid of return codes in bootstrap script (`155 <https://github.com/arista-eosplus/ztpserver/issues/155>`_)
    .. comment
* Bootstrap script should always log a detailed message before exiting (`153 <https://github.com/arista-eosplus/ztpserver/issues/153>`_)
    bootstrap script will log the reason for exiting, instead of an error code.
* Client should report what the error code means (`150 <https://github.com/arista-eosplus/ztpserver/issues/150>`_)
    .. comment
* Improve server logs when server does not know about the node (`145 <https://github.com/arista-eosplus/ztpserver/issues/145>`_)
    .. comment
* Configurable verbosity for logging options (server side) (`140 <https://github.com/arista-eosplus/ztpserver/issues/140>`_)
    Bootstrap configuration file can now specify the verbosity of client-side logs:
    ::

        ...
        xmpp:
        username: ztps
        password: ztps
        domain: pcknapweed.lab.local
        <b>msg_type : debug</b>
        rooms:
            - ztps-room

    The allowed values are:

    - debug: verbose logging
    - info: log only messages coming from the server (configured in definitions)

    The information is transmitted to the client via the bootstrap configuration request:
    ::

        ####GET logging configuration
        Returns the logging configuration from the server.

            GET /bootstrap/config

        Request

            Content-Type: text/html

        Response

            Status: 200 OK
            Content-Type: application/json
            {
                “logging”*: [ {
                    “destination”: “file:/<PATH>” | “<HOSTNAME OR IP>:<PORT>”,   //localhost enabled
                                                                                //by default
                    “level”*:        <DEBUG | CRITICAL | ...>,
                } ]
            },
                “xmpp”*:{
                    “server”:           <IP or HOSTNAME>,
                    “port”:             <PORT>,                 // Optional, default 5222
                    “username”*:        <USERNAME>,
                    “domain”*:          <DOMAIN>,
                    “password”*:        <PASSWORD>,
                    “nickname”:         <NICKNAME>,             // REMOVED
                    “rooms”*:           [ <ROOM>, … ]   
                    “msg_type”:         [ “info” | “debug” ]    // Optional, default “debug”     

                }
            }

        >**Note**: * Items are mandatory (even if value is empty list/dict)

    P.S. (slightly unrelated) The nickname configuration has been deprecated (serialnumber is used instead).
* Configurable logging levels for xmpp (`139 <https://github.com/arista-eosplus/ztpserver/issues/139>`_)
    bootstrap.conf:
    ::

        logging:
        ...
        xmpp:
        ...
        nickname: ztps        // (unrelated) this was removed - using serial number instead
        msg_type: info        // allowed values ['info', 'debug']

    If msg_type is set to 'info', only log via XMPP error messages and 'onstart', 'onsuccess' and 'onfailure' error messages (as configured in the definition).
* Bootstrap should rename LLDP SysDescr to "provisioning" while executing or failing (`138 <https://github.com/arista-eosplus/ztpserver/issues/138>`_)
    .. comment
* Test XMPP for multiple nodes being provisioned at the same time (`134 <https://github.com/arista-eosplus/ztpserver/issues/134>`_)
    .. comment
* Server logs should include ID (MAC/serial number) of node being provisioned (`133 <https://github.com/arista-eosplus/ztpserver/issues/133>`_)
    Most of the server logs will not be prefixed by the identifier of the node which is being provisioned - this should make debugging environments where multiple nodes are provisioned at the same time a lot easier.
* Use serial number instead of system MAC as the unique system ID (`131 <https://github.com/arista-eosplus/ztpserver/issues/131>`_)
    .. comment
* Bootstrap script should disable copp  (`122 <https://github.com/arista-eosplus/ztpserver/issues/122>`_)
    .. comment
* Bootstrap script should check disk space before downloading any resources (`118 <https://github.com/arista-eosplus/ztpserver/issues/118>`_)
    Bootstrap script will request the meta information from server, whenever it attempts to save a file to flash. This information will be used in order to check whether enough disk space is available for downloading the resource.
    ::

        ####GET action metadata
        Request action from the server.

            GET /meta/actions/NAME

        Request

            Content-Type: text/html

        Response

        Status: 200 OK
            Content-Type: application/json
            {
                “size”*:  <SIZE IN BYTES>,
                “sha1”: <HASH STRING>
            }

        >**Note**: * Items are mandatory (even if value is empty list/dict)

            Status: 404 Not found
            Content-Type: text/html

            Status: 500 Internal server error                      // e.g. permissions issues on server side
            Content-Type: text/html


* ztps should check Python version and report a sane error is incompatible version is being used to run it (`110 <https://github.com/arista-eosplus/ztpserver/issues/110>`_)
    ztps reports error if it is ran on a system with an incompatible Python version installed.
* Do not hardcode Python path  (`109 <https://github.com/arista-eosplus/ztpserver/issues/109>`_)
    .. comment
* Set XMPP nickname to serial number (`106 <https://github.com/arista-eosplus/ztpserver/issues/106>`_)
    Serial number is used as XMPP presence/nickname. For vEOS instances which don't have one configured, systemmac is used instead.
* Send serial number as XMPP presence (`105 <https://github.com/arista-eosplus/ztpserver/issues/105>`_)
    Serial number is used as XMPP presence/nickname. For vEOS instances which don't have one configured, systemmac is used instead.
* Support for EOS versions < 4.13.3 (`104 <https://github.com/arista-eosplus/ztpserver/issues/104>`_)
    ZTP Server bootstrap script now supports any EOS v4.12.x or later.
* neighbordb should not be cached (`97 <https://github.com/arista-eosplus/ztpserver/issues/97>`_)
    Neighbordb is not cached on the server side. This means that any updates to it do not require a server restart anymore.
* Definitions/actions should be loaded form disk on each GET request (`87 <https://github.com/arista-eosplus/ztpserver/issues/87>`_)
    Definitions and actions are not cached on the server side. This means that any updates to them do not require a server restart anymore.
* Fix all pylint warnings  (`83 <https://github.com/arista-eosplus/ztpserver/issues/83>`_)
    .. comment
* add_config action should also accept server-root-relative path for the URL (`71 <https://github.com/arista-eosplus/ztpserver/issues/71>`_)
    'url' atrribute in add_config action can be either a URL or a local server path.
* install_image action should also accept server-root-relative path for the URL (`70 <https://github.com/arista-eosplus/ztpserver/issues/70>`_)
    'url' atrribute in install_image action can be either a URL or a local server path.
* Server logs should be timestamped (`63 <https://github.com/arista-eosplus/ztpserver/issues/63>`_)
    All server-side logs now contain a timestamp. Use 'ztps --debug' for verbose debug output.
* After installing ZTPServer, there should be a dummy neighbordb (with comments and examples) and a dummy resource (with comments and examples) in /usr/share/ztpserver (`48 <https://github.com/arista-eosplus/ztpserver/issues/48>`_)
    .. comment
* need test coverage for InterfacePattern (`42 <https://github.com/arista-eosplus/ztpserver/issues/42>`_)
    .. comment
* test_topology must cover all cases (`40 <https://github.com/arista-eosplus/ztpserver/issues/40>`_)
    .. comment

Resolved issues
^^^^^^^^^^^^^^^

* Syslog messages are missing system-id (vEOS) (`184 <https://github.com/arista-eosplus/ztpserver/issues/184>`_)
    All client-side log message are prefixed by the serial number for now (regardless of what the identifier is configured on the server).

    For vEOS, if the system does not have a serial number configured, the system MAC will be used instead.
* No logs while executing actions (`182 <https://github.com/arista-eosplus/ztpserver/issues/182>`_)
    .. comment
* test_repository.py is leaking files (`174 <https://github.com/arista-eosplus/ztpserver/issues/174>`_)
    .. comment
* Allocate function will return some SysMac in quotes, others not (`137 <https://github.com/arista-eosplus/ztpserver/issues/137>`_)
    .. comment
* Actions which don't require any attributes are not supported (`129 <https://github.com/arista-eosplus/ztpserver/issues/129>`_)
    .. comment
* Static pattern validation fails in latest develop branch (`128 <https://github.com/arista-eosplus/ztpserver/issues/128>`_)
    .. comment
* Have a way to disable topology validation for a node with no LLDP neighbors (`127 <https://github.com/arista-eosplus/ztpserver/issues/127>`_)
    COPP is disabled during the bootstrap process for EOS v4.13.x and later. COPP is not supported for older releases.
* Investigate "No loggers could be found for logger sleekxmpp.xmlstream.xmlstream" error messages on client side (`120 <https://github.com/arista-eosplus/ztpserver/issues/120>`_)
    .. comment
* ZTPS should not fail if no variables are defined in neighbordb  (`114 <https://github.com/arista-eosplus/ztpserver/issues/114>`_)
    .. comment
* ZTPS should not fail if neighbordb is missing (`113 <https://github.com/arista-eosplus/ztpserver/issues/113>`_)
    .. comment
* ZTPS installation should create dummy neighbordb (`112 <https://github.com/arista-eosplus/ztpserver/issues/112>`_)
    ZTP Server install will create a placeholder neighbordb with instructions.
* Deal more gracefully with invalid YAML syntax in resource files (`75 <https://github.com/arista-eosplus/ztpserver/issues/75>`_)
    .. comment
* Server reports AttributeError if definition is not valid YAML (`74 <https://github.com/arista-eosplus/ztpserver/issues/74>`_)
    .. comment
* fix issue with Pattern creation from neighbordb (`44 <https://github.com/arista-eosplus/ztpserver/issues/44>`_)
    .. comment

