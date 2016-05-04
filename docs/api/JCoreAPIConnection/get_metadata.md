# `get_metadata([request])`

Gets metadata about channel(s), for instance the name and units.

### Arguments

* [channelids] *(string|list)*: channel id(s) to get data for (defaults to all channels)

### Returns

*(dict)*: A parsed [JSON Metadata message](../schema/metadata.md).

### Raises

* `JCoreAPIAuthException`: if authentication is required and the connection is not authenticated.
* `JCoreAPITimeoutException`: if the request times out.
* `JCoreAPIConnectionClosedException`: if the connection closes or was already closed.
* `JCoreAPIErrorResponseException`: if the server responds with an error.
* `JCoreAPIInvalidMessageException`: if the client receives an invalid response.

### Example

```py
from jcore_api import connect_local

conn = connect_local()

conn.get_metadata(['andysDevice.analog1', 'andysDevice.analog2'])
# returns {u'andysDevice.analog1': {u'units': u'V', u'max': 200, u'precision': 1, u'name': u'Analog 1', u'min': 0}, u'andysDevice.analog2': {u'units': u'V', u'max': 5, u'precision': 1, u'name': u'Analog 2', u'min': 0}}
```
