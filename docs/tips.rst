Tips and tricks
===============

.. contents:: :local:

How do I update my local copy of ZTPServer from GitHub?
````````````````````````````````````````````````````````

Automatically
^^^^^^^^^^^^^

Go to the ZTPServer directory where you previously cloned the GitHub repository and execute:
    ``./utils/refresh_ztps [-b <branch>] [-f <path>]``

    * <branch> can be any branch name in the Git repo.   Typically this will be one of:

        * "master" - for the latest release version
        * "vX.Y.Z-rc" - for beta testing the next X.Y.Z release-candidate
        * "develop" (DEFAULT) - for the latest bleeding-edge development branch

    * <path> is the base directory of the ztpserver installation.

        * /usr/share/ztpserver (DEFAULT)

Manually
^^^^^^^^

Remove the existing ZTPServer files:

.. code-block:: console

    rm -rf /usr/share/ztpserver/actions/*
    rm -rf /usr/share/ztpserver/bootstrap/*
    rm -rf /usr/lib/python2.7/site-packages/ztpserver*
    rm -rf /bin/ztps*
    rm -rf /home/ztpuser/ztpserver/ztpserver.egg-info/
    rm -rf /home/ztpuser/ztpserver/build/*

Go to the ZTPServer directory where you previously cloned the GitHub repository, update it, then build and install the server:

.. code-block:: console

    bash-3.2$ git pull
    bash-3.2$ python setup.py build
    bash-3.2$ python setup.py install

My server keeps failing to load my resource files. What’s going on?
````````````````````````````````````````````````````````````````````

Did you know?

.. code-block:: yaml

    a:b is INVALID YAML
    a: b is VALID YAML syntax

Check out `YAML syntax checker <http://yamllint.com/>`_ for more.

How do I disable / enable ZTP mode on a switch
``````````````````````````````````````````````

By default, any switch that does not have a ``startup-config`` will enter ZTP mode to attempt to retrieve one. This feature was introduced in EOS 3.7 for fixed devices and EOS 4.10 for modular ones. In ZTP mode, the switch sends out DHCP requests on all interfaces and **will not forward traffic** until it reboots with a config.

To cancel ZTP mode, login as admin and type ``zerotouch cancel``.  **This will trigger an immediate reload** of the switch, after which the switch will be ready to configure manually. At this point, if you ever erase the startup-config and reload, the switch will edn up ZTP mode again.

To completely disable ZTP mode, login as admin and type ``zerotouch disable``.  **This will trigger an immediate reload** of the switch after which the switch will will be ready to configure manually. If you wish to re-enable ZTP, go to configure mode and run ``zerotouch enable``.  The next time you erase the startup-config and reload the switch, the switch will end up ZTP mode again.

.. note:: vEOS instances come with a minimal startup-config so they do not boot in to ZTP mode by default.   In order to use vEOS to test ZTP, enter ``erase startup-config`` and reload.

How can I test ZTPServer without having to reboot the switch every time?
````````````````````````````````````````````````````````````````````````

From a bash shell on the switch:

.. code-block:: console

    # retrieve the bootstrap file from server
    wget http://<ZTP_SERVER>:<PORT>/bootstrap
    # make file executable
    sudo chmod 777 bootstrap
    # execute file
    sudo ./bootstrap

What is the recommended test environment for ZTPServer?
```````````````````````````````````````````````````````

The best way to learn about and test a ZTPServer environment is to build the server and virtual (vEOS) nodes with Packer.  See https://github.com/arista-eosplus/packer-ztpserver for directions.

If you setup your own environment, the following recommendations should assist greatly in visualizing the workflow and troubleshooting any issues which may arise.  The development team strongly encourages these steps as Best Practices for testing your environment, and, most of these recommendations are also Best Practices for a full deployment.

* During testing, only - run the standalone server in debug mode: ``ztps --debug`` in a buffered shell.   NOTE: do NOT use this standalone server in production, however, except in the smallest environments ( Approx 10 nodes or less, consecutively).
* Do not attempt any detailed debugging from a virtual or serial console.  Due to the quantity of information and frequent lack of copy/paste access, this if often painful.  Both suggested logging methods, below, can be configured in the :ref:`bootstrap_config`.

  * (BEST) Setup XMPP logging. There are many XMPP services available, including `ejabberd <https://www.ejabberd.im/>`_, and even more clients, such as `Adium <https://adium.im/>`_.  This will give you a single pane view of what is happening on all of your test switches.  Our demo includes ejabberd with the following configuration:

       * Server: im.ztps-test.com (or your ZTPServer IP)
       * XMPP admin user: ztpsadmin@im.ztps-test.com, passwd eosplus

  * (Second) In place of XMPP, splecify a central syslog server in the bootstrap config.

How do I override the default system-mac in vEOS?
``````````````````````````````````````````````````

Add the desired MAC address to the first line of the file /mnt/flash/system_mac_address, then reboot (Feature added in 3.13.0F)

.. code-block:: console

    [admin@localhost ~]$ echo 1122.3344.5566 > /mnt/flash/system_mac_address

How do I override the default serial number or system-mac in vEOS?
``````````````````````````````````````````````````````````````````

As of vEOS 4.14.0, the serial number and system mac address can be configured with a file in /mnt/flash/veos-config.  After modifying SERIALNUMBER or SYSTEMMACADDR, a reboot is required for the changes to take effect.

.. code-block:: console

    SERIALNUMBER=ABC12345678
    SYSTEMMACADDR=1122.3344.5566

