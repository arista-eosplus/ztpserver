Troubleshooting
===============

.. contents:: :local:

Basics
``````

When the ZTP process isn't behaving as expected, there are some basics that
should be checked regularly.

Updating to the latest Release is strongly encouraged
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ZTP Server is continually being enhanced and improved and its entirely possible that
the issue you've encountered has already been addressed, either in the documentation
such as :doc:`tips`, or in the code, itself.  Therefore, we strongly encourage anyone
experiencing difficulty to reproduce the issue on the latest release version before
opening an issue or requesting support.  See :ref:`upgrade`.

If the switch is not attempting Zero Touch Provisioning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check whether ZTP has been disabled on the switch::

    Arista#show zerotouch

Validate the ZTP Server configuration syntax
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many errors are simply due to typos or other syntax issues in config files. 
It is good practice to use the --validate option to ztps and to paste configs
in to `http://yamllint.com/` to ensure they are well-formed YAML::

    [user@ztpserver]$ ztps -–validate-config

Other troubleshooting steps
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of other troubleshooting steps including how to specify the separate 
apache log files just for ZTP Server, and how to do a test run of ztpserver
without reloading a switch are located on the :doc:`tips` page.

.. _before-requesting-support:

Before Requesting Support
`````````````````````````

Before requesting support, it is important to perform the following steps to
collect sufficient data to reduce information requests and enable timely resolution.

Version and Install method
^^^^^^^^^^^^^^^^^^^^^^^^^^

If not already recorded in the logs, please execute ``ztps --version`` and
specify whether your installation was from source (github), pip, RPM, or
a packer-ztpserver canned VM.

Server-side logs
^^^^^^^^^^^^^^^^

The location of server-side logs may vary depending on your specific environment.

* If running ZTP Server via Apache, check the VirtualHost definition for 
  CustomLog and ErrorLog entries, otherwise, look in the default Apache logs.
  On Fedora, those will be in /var/log/httpd/
* If running the standalone ``ztps`` binary, a good choice for debugging, please
  include the ``--debug`` option.  Using ``ztps --debug 2>&1 | tee ztpserver.log`` will log
  the output to both the screen and a file.

Client-side logs
^^^^^^^^^^^^^^^^

Ensure the bootstrap client is configured to log to syslog or XMPP via
/usr/share/ztpserver/bootstrap/bootstrap.conf and include that output.  Attempting to
collect client side logs from the console frequently results in missing information
due to scroll buffers or line length.

Configuration Files
^^^^^^^^^^^^^^^^^^^

Please, also, include the files in /etc/ztpserver/ and /usr/share/ztpserver/
directories.   ``tar czvf my_ztpserver_config.tgz /etc/ztpserver/ /usr/share/ztpserver/``

