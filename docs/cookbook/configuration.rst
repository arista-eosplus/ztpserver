ZTPServer Configuration
=======================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

..  The following sections are commented out since there are bugs

..  Define the Data_Root
    --------------------

    Objective
    ^^^^^^^^^

    I know that the default location for ZTPServer files is ``/usr/share/ztpserver/``
    but I'd like to use a different location.

    Solution
    ^^^^^^^^

    Open up your ZTPServer Global Config file:

    .. code-block:: console

      admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

    Look for the line ``data_root`` and change it to the desired directory:

    .. code-block:: console

      [default]
      # Location of all ztps boostrap process data files
      data_root = /this/directory/is/better

    Explanation
    ^^^^^^^^^^^

    The ``data_root`` is critical to the operation of the ZTPServer. The server will
    look in this directory for the ``nodes/``, ``files/``, ``actions/``, ``bootstrap/``
    directories as well as your ``neighbordb`` file.  If you would like to make
    further changes to the location of these directories, see the lower section of
    ``ztpserver.conf``.

    .. End of Define the Data_Root


..  Define the Bootstrap File Location
    ----------------------------------

    Objective
    ^^^^^^^^^

    I'd like to change the filename and path of the bootstrap script.

    Solution
    ^^^^^^^^

    Open up your ZTPServer Global Config file:

    .. code-block:: console

      admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

    Look for the line ``data_root`` and change it to the desired directory:

    .. code-block:: console

      [default]
      # Location of all ztps boostrap process data files
      data_root = /this/directory/is/better

    Explanation
    ^^^^^^^^^^^

    The ``data_root`` is critical to the operation of the ZTPServer. The server will
    look in this directory for the ``nodes/``, ``files/``, ``actions/``, ``bootstrap/``
    directories as well as your ``neighbordb`` file.  If you would like to make
    further changes to the location of these directories, see the lower section of
    ``ztpserver.conf``.

    .. End of Define the Bootstrap File Location

Identify Nodes Based Upon Serial Number
---------------------------------------

Objective
^^^^^^^^^

I'd like the ZTPServer to use the switch's serial number for provisioning.  This
implies that all node directories in ``nodes/`` will be named using the serial
number.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``identifier`` and confirm it's set to ``serialnumber``:

.. code-block:: console

  identifier = serialnumber

Restart the ztps process:

.. code-block:: console

  # If using Apache WSGI
  admin@ztpserver:~# service apache2 restart

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps


Explanation
^^^^^^^^^^^

The ZTPServer will use either the System MAC Address or the Serial Number
of the switch as its System ID. The System ID is used to match statically
provisioned nodes. Also, when a node is dynamically provisioned, the ZTPServer
will create a new node directory for it in ``nodes/`` and it will be named using
the System ID.

.. End of Identify Nodes Based Upon Serial Number


Identify Nodes Based Upon System MAC Address
--------------------------------------------

Objective
^^^^^^^^^

I'd like the ZTPServer to use the switch's System MAC Address for provisioning.
This implies that all node directories in ``nodes/`` will be named using the
System MAC Address.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``identifier`` and confirm it's set to ``systemmac``:

.. code-block:: console

  identifier = systemmac

Restart the ztps process:

.. code-block:: console

  # If using Apache WSGI
  admin@ztpserver:~# service apache2 restart

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps


Explanation
^^^^^^^^^^^

The ZTPServer will use either the System MAC Address or the Serial Number
of the switch as its System ID. The System ID is used to match statically
provisioned nodes. Also, when a node is dynamically provisioned, the ZTPServer
will create a new node directory for it in ``nodes/`` and it will be named using
the System ID.

.. End of Identify Nodes Based Upon System MAC Address



Enable/Disable Topology Validation
----------------------------------

Objective
^^^^^^^^^

Topology Validation uses LLDP Neighbor information to make sure you have everything
wired up correctly. Topology Validation is enabled/disabled in the main ``ztpserver.conf``
configuration file.

Solution
^^^^^^^^

Open up the global ZTPServer configuration file:

.. code-block:: console

  admin@ztpserver:~# vi /etc/ztpserver/ztpserver.conf

Look for the line ``disable_topology_validation``

.. code-block:: console

  # To disable Topology Validation
  disable_topology_validation = True

  # To enable Topology Validation
  disable_topology_validation = False

Restart the ztps process:

.. code-block:: console

  # If using Apache WSGI
  admin@ztpserver:~# service apache2 restart

  # If running in Standalone Mode, stop ztps
  admin@ztpserver:~# pkill ztps

  # Then start it again
  admin@ztpserver:~# ztps

Explanation
^^^^^^^^^^^

This configuration option enables/disables Topology Validation. This feature
is extremely powerful and can help you confirm all of your nodes are wired up
correctly. See the recipes under :ref:`tv-reference-label` to learn more about
the flexibility of Topology Validation.

.. End of Enable/Disable Topology Validation
