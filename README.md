# jcore-api-py

Python API for communicating with a jcore.io server.

### Compatibility

This package is known to require at least Python 2.6 as it uses `bytearray`.

Tested on CPython 2.7.11 and 3.5.1.

### Installation

```
pip install jcore_api
```

### Example

(This example must be run on the same machine as the server)

```py
from jcore_api import connect_local

jcore = connect_local()

print(jcore.get_metadata())
```
