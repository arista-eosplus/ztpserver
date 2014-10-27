Tips and tricks
===============

.. contents:: :local:

How do I update my local copy of ZTPServer from GitHub?
````````````````````````````````````````````````````````

Script
^^^^^^

Go to the ZTPServer directory where you previously cloned the GitHub repository in order to pull the latest code and execute:
    ``./utils/refresh_ztps [-b <branch>] [-f <path>]``

    * <branch> can be any branch name in the Git repo.   Typically this will be one of:

        * "master" - for the latest release version
        * "vX.Y.Z-rc" - for beta testing the next X.Y.Z release-candidate
        * "develop" (DEFAULT) - for the latest bleeding-edge development branch

    * <path> is the "base directory of the ztpserver installation.

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

Go to the ZTPServer directory where you previously cloned the GitHub repository in order to pull the latest code, build and install it:

.. code-block:: console

    bash-3.2$ git pull
    bash-3.2$ python setup.py build
    bash-3.2$ python setup.py install

My server keeps failing to load my resource files. What’s going on?
````````````````````````````````````````````````````````````````````

Did you know?

.. code-block:: yaml

    a:b is INVALID YAML
    a: b is VALID YAML options

Check out `YAML syntax checker <http://yamllint.com/>`_ for more.

How do I disable / enable ZTP mode on a switch
``````````````````````````````````````````````

By default, any switch that does not have a ``startup-config`` will enter ZTP mode to attempt to retrieve one. (EOS 3.7 or later for fixed, EOS 4.10 or later for modular switches)  In ZTP mode, the switch sends out DHCP requests on all interfaces and **will not forward traffic** until reloaded out of ATP mode.

To cancel ZTP mode in order to manually login and configure a switch, login as admin and type ``zerotouch cancel``.  **This will trigger an immediate reload** of the switch, after which it will be ready to configure manually.   At this point, if you ever erase the startup-config and reload, ZTP will attempt to retrieve a configuration, again.

To completely disable ZTP, during ztp, login as admin and type ``zerotouch disable``.  **This will trigger an immediate reload** of the switch.  Afterward the switch will boot with an empty startup-config.  If you wish to re-enable ZTP, go to configure mode and add ``Arista(config)#zerotouch enable``.  The next time you erase the startup-config and reload the switch, ZTP will attempt to configure it for you.

.. note: vEOS instances come with a, minimal, startup-config so they do not boot in to ZTP mode by default.   In order to use vEOS to test ZTP, enter ``erase startup-config`` and reload.

How can I test ZTPServer without having to reboot the switch every time?
````````````````````````````````````````````````````````````````````

From a bash shell on the switch:

.. code-block:: console

    # retrieve the bootstrap file from server
    wget http://<ZTP_SERVER>:<PORT>/bootstrap
    # make file executable
    sudo chmod 777 bootstrap
    # execute file
    sudo ./bootstrap

How do I override the default system-mac in vEOS?
``````````````````````````````````````````````````

Add the desired MAC address to the first line of the file /mnt/flash/system_mac_address, then reboot

.. code-block:: console

    [admin@localhost ~]$ echo 1122.3344.5566 > /mnt/flash/system_mac_address

How do I override the default serial number or system-mac in vEOS?
``````````````````````````````````````````````````````````````````

As of vEOS 4.14.0, the serial number and system mac address can be configured with a file in /mnt/flash/veos-config.  After modifying SERIALNUMBER or SYSTEMMACADDR, a reboot is required for the changes to take effect.

.. code-block:: console

    SERIALNUMBER=ABC12345678
    SYSTEMMACADDR=1122.3344.5566

