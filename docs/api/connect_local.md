# connect_local([create_socket])

Connects to a jcore.io server on the local machine via UNIX socket.

### Arguments

1. [`create_socket`] *(Function)*: provide this function if you need to configure the socket (for instance, to use a
proxy, set the timeout, etc.).  It is passed one argument: the unix socket path, and should return an instance of
[`socket.socket`](http://devdocs.io/python/library/socket#socket.socket).

### Returns

([*Connection*](Connection/README.md)): an object that keeps track of a connection to the server and allows you to call API
methods.

### Example

```py
from socket import socket, AF_UNIX, SOCK_STREAM
from jcore_api import connect_local

def create_socket(path):
  sock = socket(AF_UNIX)
  sock.settimeout(30)
  sock.connect(path)
  return sock

conn = connect_local(create_socket)
```
