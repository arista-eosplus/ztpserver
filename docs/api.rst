Client - Server API
-------------------

.. contents:: :local:

URL Endpoints
~~~~~~~~~~~~~

+---------------+-------------------------------+
| HTTP Method   | URI                           |
+===============+===============================+
| GET           | /bootstrap/config             |
+---------------+-------------------------------+
| GET           | /bootstrap                    |
+---------------+-------------------------------+
| POST          | /nodes                        |
+---------------+-------------------------------+
| PUT           | /nodes/{id}                   |
+---------------+-------------------------------+
| GET           | /nodes/{id}                   |
+---------------+-------------------------------+
| GET           | /actions/{name}               |
+---------------+-------------------------------+
| GET           | /files/{filepath}             |
+---------------+-------------------------------+

GET bootstrap script
^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap

    Returns the default bootstrap script

    **Response**

    .. code-block:: http

        Status: 200 OK
        Content-Type: text/x-python

.. note::

    For every request, the bootstrap controller on the
    ZTPServer will attempt to perform the following string replacement
    in the bootstrap script): **“$SERVER“ ---> the value of the
    “server\_url” variable in the server’s configuration file** This
    string-replacement will point the bootstrap client back to the
    server, in order to enable it to make additional requests for
    further resources.

-  if the ``server_url`` variable is missing in the server’s
   configuration file, 'http://ztpserver:8080' is used by default
-  if the ``$SERVER`` string does not exist in the bootstrap script, the
   controller will log a warning message and continue

GET logging configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /bootstrap/config

    Returns the logging configuration from the server.

    **Request**

    .. sourcecode:: http

        GET /bootstrap/config HTTP/1.1
        Host: 
        Accept: 
        Content-Type: text/html

    **Response**

    .. sourcecode:: http

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
                “nickname”:         <NICKNAME>,             // Optional, default ‘username’
                “rooms”*:           [ <ROOM>, … ]                     
                }
            }
        }

    **Note**: \* Items are mandatory (even if value is empty list/dict)

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

    .. sourcecode:: http 

        Status: 201 Created
        Content-Type: text/html
        Location: <url>

        Status: 409 Conflict
        Content-Type: text/html
        Location: <url>

        Status: 400 Bad Request
        Content-Type: text/html

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
        Host: 
        Accept: applicatino/json
        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Status: 200 OK
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

    :statuscode 400: Bad Request
    :statuscode 404: Not Found

GET action
^^^^^^^^^^

.. http:get:: /actions/(NAME)

I   Request action from the server.

    **Request**

    .. sourcecode:: http

        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Content-Type: text/x-python

    :statuscode 200: OK
    :statuscode 400: Bad Request
    :statuscode 404: Not Found

    Status: 200 OK
    Content-Type: text/plain
    <PYTHON SCRIPT>

    Status: 200 Bad request
    Content-Type: text/x-python

GET resource
^^^^^^^^^^^^

.. http:get::  /files/(RESOURCE_PATH)

    Request action from the server.

    **Request**

    .. sourcecode:: http

        Content-Type: text/html

    **Response**

    .. sourcecode:: http

        Status: 200 OK
        Content-Type: text/plain
        <resource>

    :statuscode 200: OK
    :statuscode 404: Not Found

