Client - Server API
-------------------

.. The RESTful API is documented using sphinxcontrib-httpdomain.  See
   http://pythonhosted.org/sphinxcontrib-httpdomain/

.. Verify sync with ztpserver.controller.py using the following:
   (PYTHONPATH=.; python)
   my_map = controller.Router()
   print(my_map.map)

.. contents:: :local:

URL Endpoints
~~~~~~~~~~~~~

+---------------+-----------------------------------------+
| HTTP Method   | URI                                     |
+===============+=========================================+
| GET           | /bootstrap                              |
+---------------+-----------------------------------------+
| GET           | /bootstrap/config                       |
+---------------+-----------------------------------------+
| POST          | /nodes                                  |
+---------------+-----------------------------------------+
| GET           | /nodes/{id}                             |
+---------------+-----------------------------------------+
| PUT           | /nodes/{id}/startup-config              |
+---------------+-----------------------------------------+
| GET           | /nodes/{id}/startup-config              |
+---------------+-----------------------------------------+
| GET           | /actions/{name}                         |
+---------------+-----------------------------------------+
| GET           | /files/{filepath}                       |
+---------------+-----------------------------------------+
| GET           | /meta/{actions|files|nodes}/{PATH_INFO} |
+---------------+-----------------------------------------+

GET bootstrap script
^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap

    Returns the default bootstrap script

    **Request**

    .. sourcecode:: http

        GET /bootstrap HTTP/1.1

    **Response**

    .. code-block:: http

        Content-Type: text/x-python
        <contents of bootstrap client script>

    :resheader Content-Type: text/x-python
    :statuscode 200: OK

.. note::

    For every request, the bootstrap controller on the
    ZTPServer will attempt to perform the following string replacement
    in the bootstrap script): **“$SERVER“ ---> the value of the
    “server\_url” variable in the server’s global configuration file**. This
    string replacement will point the bootstrap client back to the
    server in order to enable the client to make additional requests for
    further resources on the server.

-  if the ``server_url`` variable is missing from the server’s global
   configuration file, 'http://ztpserver:8080' is used by default
-  if the ``$SERVER`` string is missing from the bootstrap script, the
   controller will log a warning message and continue

GET bootstrap logging configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap/config

    Returns the logging configuration from the server.

    **Request**

    .. sourcecode:: http

        GET /bootstrap/config HTTP/1.1

    **Response**

    .. sourcecode:: http

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
                “nickname”:         <NICKNAME>,             // Optional, default ‘username’
                “rooms”*:           [ <ROOM>, … ]
                }
            }
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    :resheader Content-Type: application/json
    :statuscode 200: OK

POST node details
^^^^^^^^^^^^^^^^^

Send node information to the server in order to check whether it can be
provisioned.

.. http:post:: /nodes

    **Request**

    .. sourcecode:: http

        Content-Type: application/json
        {
            “model”*:             <MODEL_NAME>, 
            “serialnumber”*:      <SERIAL_NUMBER>, 
            “systemmac”*:         <SYSTEM_MAC>,
            “version”*:           <INTERNAL_VERSION>, 
            “neighbors”*: {
                <INTERFACE_NAME(LOCAL)>: [ {
                    'device':             <DEVICE_NAME>, 
                    'remote_interface':   <INTERFACE_NAME(REMOTE)>
                } ]
            }, 
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    **Response**

    Status: 201 Created OR 409 Conflict will both return:

    .. sourcecode:: http 

        Content-Type: text/html
        Location: <url>

    :statuscode 201: Created
    :statuscode 409: Conflict
    :statuscode 400: Bad Request

GET node definition
^^^^^^^^^^^^^^^^^^^

Request definition from the server.

.. http:get:: /nodes/(ID)

    **Request**

    .. sourcecode:: http

        GET /nodes/{ID} HTTP/1.1
        Accept: application/json

    **Response**

    .. sourcecode:: http

        Content-Type: application/json
        {
            “name”*: <DEFINITION_NAME>

            “actions”*: [{ “action”*:         <NAME>*,
                        “description”:     <DESCRIPTION>,
                        “onstart”:         <MESSAGE>,
                        “onsuccess”:       <MESSAGE>,
                        “onfailure”:       <MESSAGE>,
                        “always_execute”:  [True, False],
                        “attributes”: { <KEY>: <VALUE>,
                                        <KEY>: { <KEY> : <VALUE>},
                                        <KEY>: [ <VALUE>, <VALUE> ]
                                        }
                        },...]
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

    :resheader Content-Type: application/json
    :statuscode 200: OK
    :statuscode 400: Bad Request
    :statuscode 404: Not Found

PUT node startup-config
^^^^^^^^^^^^^^^^^^^^^^^

This is used to backup the startup-config from a node to the server.

.. http:put:: /nodes/(ID)/startup-config

    **Request**

    .. sourcecode:: http

        Content-Type: text/plain
        <startup-config contents>

    :statuscode 201: Created
    :statuscode 400: Bad Request

GET node startup-config
^^^^^^^^^^^^^^^^^^^^^^^

This is used to retrieve the startup-config that was backed-up from a node to the server.

.. http:get:: /nodes/(ID)/startup-config

    **Request**

    .. sourcecode:: http

        Content-Type: text/plain

    **Response**

    Status: 201 Created OR 409 Conflict will both return:

    .. sourcecode:: http 

        Content-Type: text/plain
        <startup-config contents>

    :resheader Content-Type: text/plain
    :statuscode 200: OK
    :statuscode 400: Bad Request

GET actions/(NAME)
^^^^^^^^^^^^^^^^^^

.. http:get:: /actions/(NAME)

    Request action from the server.

    **Request Example**

    .. sourcecode:: http

        GET /actions/add_config HTTP/1.1

    **Response**

    .. sourcecode:: http

        Content-Type: text/x-python
        <raw action content>

    :resheader Content-Type: text/x-python
    :statuscode 200: OK
    :statuscode 404: Not Found

GET resource files
^^^^^^^^^^^^^^^^^^

.. http:get::  /files/(RESOURCE_PATH)

    Request action from the server.

    **Request Examples**

    .. sourcecode:: http

        GET /files/images/vEOS.swi HTTP/1.1
        GET /files/templates/ma1.template HTTP/1.1

    **Response**

    .. sourcecode:: http

        <raw resource contents>

    :resheader Content-Type:text/plain
    :statuscode 200: OK
    :statuscode 404: Not Found

GET meta data for a resource or file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get::  /meta/(actions|files|nodes)/(PATH_INFO)

    Request meta-data on a file.

    **Example Requests**

    .. sourcecode:: http

        GET /meta/actions/add_config HTTP/1.1
        GET /meta/files/images/EOS-4.14.5F.swi HTTP/1.1
        GET /meta/nodes/001122334455/.node HTTP/1.1

    **Response**

    .. sourcecode:: http

        {
          sha1: "d3852470a7328a4aad54ce030c543fdac0baa475"
          size: 160
        }

    :resheader Content-Type:application/json
    :statuscode 200: OK
    :statuscode 500: Server Error
