Definitions
===========

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Add an Action to a Definition
-----------------------------

Objective
^^^^^^^^^

I want to use one of the built-in actions in my definition file.

Solution
^^^^^^^^

You can choose any of the pre-built actions to include in your definition.

.. note:: Learn more about `Actions <http://ztpserver.readthedocs.org/en/master/config.html#actions>`_.

In this example we'll copy a python script to the node and set its permissions.

.. code-block:: yaml

  ---
  actions:
    -
      action: copy_file
      always_execute: true
      attributes:
        dst_url: /mnt/flash/
        mode: 777
        overwrite: if-missing
        src_url: files/automate/bgpautoinf.py
      name: "automate BGP peer interface config"

Explanation
^^^^^^^^^^^

Here we add the ``copy_file`` action to our definition. The attributes listed in
the action will be passed to the node so that it is able to retrieve the script
from ``[SERVER_URL]/files/automate/bgpautoinf.py``. Since we are using ``overwrite: if-missing``,
the action will only copy the file to the node if it does not already exist.

.. note:: For more Action recipes see the Actions section.

.. End of Add an Action to a Definition



Add Global Variables to Definition
----------------------------------

Objective
^^^^^^^^^

I want to use a variable throughout my definition without having to define it
more than once.

Solution
^^^^^^^^

You can accomplish this by adding an ``attributes`` section at the root level of
your definition file.

.. note:: Learn more about `Actions <http://ztpserver.readthedocs.org/en/master/config.html#actions>`_.

In this example, we have two different actions that reference the same ``$mode``
and ``$dst`` variables.

.. code-block:: yaml

  ---
  actions:
    -
      action: copy_file
      always_execute: true
      attributes:
        dst_url: $dst
        mode: $mode
        overwrite: if-missing
        src_url: files/automate/bgpautoinf.py
      name: "Copy automate BGP script to node"
    -
      action: copy_file
      always_execute: true
      attributes:
        dst_url: $dst
        mode: $mode
        overwrite: if-missing
        src_url: files/automate/superautomate.py
      name: "Copy awesome script to my node"
    -
      action: add_config
      attributes:
        url: files/templates/ma1.template
        variables:
          ipaddress: $ip
      name: "configure ma1"
    -
      action: add_config
      attributes:
        url: files/templates/xmpp.template
        variables: $variables
      name: "configure ma1"

  attributes:
    dst: /mnt/flash
    mode: 777
    ip: 192.168.0.50
    variables:
      domain: im.example.com
      user: myXmmpUser
      passwd: secret
      room: myAwesomeRoom


Explanation
^^^^^^^^^^^

This example shows how to use global variables within the definition. It's
important to see the difference between using variables to define attributes
of the action versus variables that get used within the template in an
``add_config`` action.  See how the ``ipaddress`` variable is nested within
a ``variables`` key?  Also, you can create a list in the ``attributes`` section
and pass the entire list into the action as shown in the XMPP config action.

.. note:: For more Action recipes see the Actions section.

.. End of Add an Action to a Definition






Add Custom Log Statements as Action Executes
--------------------------------------------

Objective
^^^^^^^^^

I want to send specific messages to my syslog and/or XMPP servers while an action
is executing. Especially, if something goes wrong, I'd like to add a helpful message
so the engineer knows who to contact.

Solution
^^^^^^^^

The node being provisioned will send predefined logs to the endpoints defined in
``[data_root]/bootstrap/bootstrap.conf``, but you can send additional client-side
logs by adding a few attributes to your definition.

Let's add some specific status messages to the definition below.

.. note:: This could be a static node definition in ``[data_root]/nodes/<SYSTEM_ID>/definition``
          or a global definition in ``[data_root]/definitions/definition_name``.

.. code-block:: yaml

  ---
  actions:
    -
      action: copy_file
      always_execute: true
      attributes:
        dst_url: $dst
        mode: $mode
        overwrite: if-missing
        src_url: files/automate/bgpautoinf.py
      name: "Copy automate BGP script to node"
      onstart: "Starting the action to copy the BGP script"
      onsuccess: "SUCCESS: The BGP script has been copied"
      onfailure: "ERROR: Failed to copy script - contact admin@example.com"
  attributes:
    dst: /mnt/flash
    mode: 777

Explanation
^^^^^^^^^^^

Here we make use of three specific keywords: ``onstart``, ``onsuccess`` and
``onfailure``. By adding these keys to your definition, the node will generate
this message while it is being provisioned. As mentioned above, this message will
be sent to all of the logging destinations defined in ``[data_root]/bootstrap/bootstrap.conf``.

.. note:: For help defining an XMPP or syslog endpoint, see :ref:`client-logging-label`

.. End of Add an Action to a Definition
