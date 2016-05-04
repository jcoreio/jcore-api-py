# `set_real_time_data(data)`

Sets the values of channel(s).

### Arguments

* data *(dict)*: map from channel id *(string)* to a *(dict)* that can be serialized to a
  [JSON Real-Time Data message](../schema/realTimeData.md) by [json.dumps](http://devdocs.io/python/library/json#json.dumps).
  If any of the given channel ids don't exist, the values will be stored, but they won't be visible until metadata is
  created for those channels.

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

conn.set_real_time_data({'helloworld': 123456})
conn.get_real_time_data('helloworld')
# returns {u'timestamp': u'2016-05-03T23:21:10.754Z', u'data': {u'helloworld': 123456}}
```
