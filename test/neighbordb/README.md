This directory holds test definitions for testing nodes and patterns against neighbordb.  Each folder represents a set that includes a neighbordb pattern file, a test_definition file and one or more node JSON files.

* Step 1: To create a new test case create a new folder in test/neighbordb
* Step 2: Create a neighbordb pattern file just as you would for a server implementation
* Step 3: Create node JSON files using the following format:
```
    {
        "model": "vEOS",
        "serialnumber": "1234567890",
        "systemmac": "00:1c:73:1a:2b:3d",
        "version": "4.12.0",
        "neighbors": {
            "Ethernet1": [{ "device": "pod1-spine1", "port": "Ethernet1" }],
            "Ethernet2": [{ "device": "pod1-spine2", "port": "Ethernet1" }],
            "Ethernet6": [{ "device": "spine4", "port": "Ethernet8" },
                          { "device": "spine5", "port": "Ethernet2" }],
            "Ethernet7": [{ "device": "spine4", "port": "Ethernet8" },
                          { "device": "spine5", "port": "Ethernet2" }],
            "Ethernet49": [{ "device": "localhost", "port": "Ethernet49" }],
            "Ethernet50": [{ "device": "localhost", "port": "Ethernet50" }]
        }
    }
```
* Step 4: Create a test_definition file using the following format:

```
    name: sample pattern test
    neighbordb: neighbordb
    nodes:
      - node: 2b3d.json
        matches: 4
        match_includes:
          - pattern 1
          - pattern 2
        match_excludes:
          - pattern 3
          - pattern 4

      - node: d27d.json
        matches: 1
        match_includes:
          - pattern 3
```

