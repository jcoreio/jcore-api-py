# `connect(api_token, [create_socket], [**kwargs])`

Connects to a jcore.io server via WebSocket and authenticates with the given api token.

### Arguments

1. `api_token` *(string)*: an API token from a jcore.io server; it is base64 encoded and contains the URL of the server.

2. [`create_socket`] *(Function)*: provide this function if you need to configure the WebSocket (for instance, to use a
proxy, set the timeout, etc.).  It is passed one argument: the `url` to connect to, and should return an instance of
[`websocket.WebSocket`](https://github.com/liris/websocket-client).

3. [`**kwargs`]: named options for the `JCoreAPIConnection`.  Includes:
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
from websocket import WebSocket
from jcore_api import connect

TOKEN = "eyJ1cmwiOiJ3czovL2xvY2FsaG9zdDozMDMwL2pjb3JlLWFwaSIsInRva2VuIjoiRWpITEkvcFlpOWxrbldUL2E5dEJnNlY2Um9pdXhsTEZJOUdMTUJUYk9oQm15bko1ZFlGRGZWRVJ3YnJmUlFWcSJ9"

def create_socket(url):
  sock = WebSocket()
  sock.settimeout(30)
  sock.connect(url)
  return sock

conn = connect(TOKEN, create_socket)
```
