# `set_metadata(metadata)`

Sets metadata about channel(s), for instance the name and units.

### Arguments

* metadata *(dict)*: a map from channel id *(string)* to a *dict* that can be serialized to a
  [JSON Metadata message](../schema/metadata.md) by [json.dumps](http://devdocs.io/python/library/json#json.dumps).
  If any of the given channel ids don't exist, they will be created and populated with default values before being
  set.

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

conn.set_metadata({'helloworld': {'name': 'Hello World'}})
conn.get_metadata('helloworld')
# returns {u'helloworld': {u'max': 200, u'precision': 1, u'name': u'Hello World', u'min': 0}}
```
