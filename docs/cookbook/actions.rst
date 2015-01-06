Action Recipes
==============

.. The line below adds a local TOC

.. contents:: :local:
  :depth: 1

Add a configuration block to a node
-----------------------------------

Objective
^^^^^^^^

In order to keep your provisioning data modular, you may want to break apart
configuration blocks into small code blocks. You can use the ``add_config``
action to place a block on code on the node.

Solution
^^^^^^^^

First, add the ``add_config`` action to your definition:

.. code-block:: yaml

    ---
    actions:
      -
        action: add_config
        attributes:
          url: files/templates/ma1.template
          variables:
            ipaddress: allocate('mgmt_subnet')
        name: "configure ma1"

Contents of ``files/templates/ma1.template``:

.. code-block:: yaml

    interface Management1
      ip address $ipaddress
      no shutdown

Explanation
^^^^^^^^^^^

Here we defined a simple action that adds configuration for interface Ma1.
The ``url`` in this case is a relative path and the full path is interpreted as
``data_root``/url. The use of ``variables`` is optional, but it allows us to
create a generic ``ma1.template`` and then use a resource pool to dynamically
assign an IP Address to the interface.
