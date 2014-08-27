Tips and tricks
===============

.. contents:: :local:

How do I update my local copy of ZTPServer from GitHub?
````````````````````````````````````````````````````````

Script
^^^^^^

Go to the ZTPS directory where you previously cloned the GitHub repository in order to pull the latest code and execute:
    ``/utils/refresh_ztps``

Manually
^^^^^^^^

Remove the existing ZTPS files:

.. code-block:: console

    rm -rf /usr/share/ztpserver/actions/*
    rm -rf /usr/share/ztpserver/bootstrap/*
    rm -rf /usr/lib/python2.7/site-packages/ztpserver*
    rm -rf /bin/ztps*
    rm -rf /home/ztpuser/ztpserver/ztpserver.egg-info/
    rm -rf /home/ztpuser/ztpserver/build/*

Go to the ZTPS directory where you previously cloned the GitHub repository in order to pull the latest code, build an install it:

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

How can I test ZTPS without having to reboot the switch every time?
````````````````````````````````````````````````````````````````````

From a bash shell:

.. code-block:: console

    # retrieve the bootstrap file from server
    wget (http://<ZTPS_SERVER>:<PORT>/bootstrap
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

