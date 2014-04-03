This directory holds test definitions for testing nodes and patterns against neighbordb.  Each file represents a test that includes a neighbordb pattern and a test_definition.

* Step 1: To create a new test case create a new YAML file in test/neighbordb (name must end in '_test')
* Step 2: Add neighbordb pattern to YAML file
* Step 3: Create node information to YAML file

Example:

   name: example test

   neighbordb:
     variables:
       ny_pod: regex("ny\d+")

     patterns:
       - name: sample node template 1
         definition: test
         node: 000c29f5d27da
         interfaces:
           - Ethernet1: any
           - Ethernet3: localhost:Ethernet1
           - Ethernet49: localhost:Ethernet49
           - Ethernet50:
               device: localhost
               port: Ethernet50

   nodes:
     - node: 2b3d.json
       details: 
         model: vEOS
         serialnumber: 1234567890
         systemmac: 00:1c:73:1a:2b:3d
         version: 4.12.0
         neighbors:
           Ethernet1:
               - 
                 device: pod1-spine1
                 port: Ethernet1
       matches: 0
       match_includes:
         - sample node template 1


