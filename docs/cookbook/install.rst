Installation
============

**Recipes**

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Install ZTPServer from Github Source
------------------------------------

Objective
^^^^^^^^^

I want to install ZTPServer from source.

Solution
^^^^^^^^

To install the latest code in `development <https://github.com/arista-eosplus/ztpserver/tree/develop>`_:

.. code-block:: console

  # Change to desired download directory
  mkdir -p ~/arista
  cd ~/arista
  git clone https://github.com/arista-eosplus/ztpserver.git
  cd ztpserver
  python setup.py build
  python setup.py install

Or, to install a specific `tagged release <https://github.com/arista-eosplus/ztpserver/releases>`_:

.. code-block:: console

  # Change to desired download directory
  mkdir -p ~/arista
  cd ~/arista
  git clone https://github.com/arista-eosplus/ztpserver.git
  cd ztpserver
  git checkout v1.2.0
  python setup.py build
  python setup.py install

Explanation
^^^^^^^^^^^

Github is used to store the source code for the ZTPServer and the ``develop``
branch always contains the latest publicly available code. The first method above
clones the git repo and automatically checks out the ``develop`` branch. We then
``build`` and ``install`` using Python.

The second method uses the ``git checkout`` command to set your working
directory to a specific release of the ZTPServer.  Both methods of installation
will produce the files below.

**Important Installation Files**

* ZTPServer Global Configuration File: ``/etc/ztpserver/ztpserver.conf``
* ZTPServer WSGI App: ``/etc/ztpserver/ztpserver.wsgi``
* ZTPServer Provisioning Files: ``/usr/share/ztpserver/`` known as ``data_root``
* Bootstrap Config File: ``/usr/share/ztpserver/bootstrap/bootstrap.conf``
* Bootstrap Python Script: ``/usr/share/ztpserver/bootstrap/bootstrap``

.. End of Install ZTPServer from Github Source



Install ZTPServer using PIP
---------------------------

Objective
^^^^^^^^^

Install ZTPServer using PyPI(pip)

Solution
^^^^^^^^

This option assumes you have a server with Python and pip pre-installed.
See `installing pip <https://pip.pypa.io/en/latest/installing.html>`_.

Once pip is installed, type:

.. code-block:: console

    pip install ztpserver

Explanation
^^^^^^^^^^^

The pip install process will install all dependencies and run the install script,
leaving you with a ZTPServer instance ready to configure.

**Important Installation Files**

* ZTPServer Global Configuration File: ``/etc/ztpserver/ztpserver.conf``
* ZTPServer WSGI App: ``/etc/ztpserver/ztpserver.wsgi``
* ZTPServer Provisioning Files: ``/usr/share/ztpserver/`` known as ``data_root``
* Bootstrap Config File: ``/usr/share/ztpserver/bootstrap/bootstrap.conf``
* Bootstrap Python Script: ``/usr/share/ztpserver/bootstrap/bootstrap``

.. End of Install ZTPServer using PIP
