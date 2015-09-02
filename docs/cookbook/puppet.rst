Puppet Agent - Bootstrap EOS
============================

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Bootstrap EOS to Puppet
-----------------------

Objective
^^^^^^^^^

I want to bootstrap an EOS node with the Puppet agent.

Solution
^^^^^^^^

.. note:: Prior to EOS 4.14.5, eAPI must be configured with HTTPS or HTTP and a flash:eapi.conf must be created for rbeapi.  Starting with EOS 4.14.5, rbeapi can use unix-sockets to communicate with eAPI, locally.

Download the `Puppet Enterprise agent <https://puppetlabs.com/download-puppet-enterprise-all#agent>`_ (may be used with Puppet Enterprise or Open Source) from PuppetLabs and the `Ruby client for eAPI (pe-rbeapi) <https://github.com/arista-eosplus/rbeapi/releases>`_ SWIX from GitHub.  Place these files in /usr/share/ztpserver/files/puppet/``

.. code-block:: yaml

  ---
  name: puppet-test
  actions:
    -
      name: "Install Puppet agent"
      action: install_extension
      always_execute: true
      attributes:
        url: files/puppet/puppet-enterprise-3.8.2-eos-4-i386.swix
    -
      name: "Install rbeapi - Ruby client for eAPI"
      action: install_extension
      always_execute: true
      attributes:
        url: files/puppet/rbeapi-0.3.0.swix
    -
      name: "Configure host alias and eAPI for Puppet"
      action: add_config
      attributes:
        url: files/templates/puppet.template
        variables:
          hostname: allocate('mgmt_hostnames')
          domainname: example.com
          puppetmaster: 172.16.130.10
          ntpserver: 66.175.209.17
      onstart: "Starting to configure EOS for Puppet"
      onsuccess: "SUCCESS: Base config for Puppet"

.. code-block:: console

  !
  alias puppet bash sudo /opt/puppet/bin/puppet
  !
  hostname $hostname
  !
  ip domain-name $domainname
  !
  ip host puppet $puppetmaster
  !
  ntp server $ntpserver prefer iburst
  !
  management api http-commands
     no protocol https
     protocol unix-socket
     no shutdown
  !

Explanation
^^^^^^^^^^^

Here we use the ``install_extension`` action to install the Puppet agent and
Ruby client for eAPI, then apply a minimal configuration so the Puppet agent
can generate its SSL keys and contact the Puppet Master. The attributes listed
in the ``add_config`` action will be passed to the node so that it is able to
properly generate its SSL keypair and certificate signing request (CSR) and
validate the Puppet master's certificate.

.. note:: For more Action recipes see the Actions section.

.. End of Bootstrap a Puppet node
