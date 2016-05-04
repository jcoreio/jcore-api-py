# `connect_local([create_socket], [**kwargs])`

Connects to a jcore.io server on the local machine via UNIX socket.  Unlike [`connect`](connect.md), this does not
require authentication.

### Arguments

1. [`create_socket`] *(Function)*: provide this function if you need to configure the socket (for instance, to use a
proxy, set the timeout, etc.).  It is passed one argument: the unix socket path, and should return an instance of
[`socket.socket`](http://devdocs.io/python/library/socket#socket.socket).

2. [`**kwargs`]: named options for the `JCoreAPIConnection`.  Includes:
  * [`on_unexpected_exception`] *(Function)*: if provided, this will be called if an unexpected exception occurs while
    the connection is handling a message it received from the server.  It is called with the output of `sys.exc_info()`.


### Returns

([*JCoreAPIConnection*](JCoreAPIConnection/README.md)): an object that keeps track of a connection to the server and allows you to call API
methods.

### Raises

* `JCoreAPIAuthException`: if authentication fails.
* `JCoreAPITimeoutException`: if authentication times out.
* `JCoreAPIConnectionClosedException`: if the connection closes during authentication.

### Example

```py
from socket import socket, AF_UNIX
from jcore_api import connect_local

def create_socket(path):
  sock = socket(AF_UNIX)
  sock.settimeout(30)
  sock.connect(path)
  return sock

conn = connect_local(create_socket)
```
