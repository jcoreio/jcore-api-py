# `get_metadata([request])`

Gets metadata about channel(s), for instance the name and units.

### Arguments

* [channelids] *(string|list)*: channel id(s) to get data for (defaults to all channels)

### Returns

*(dict)*: A parsed [JSON Metadata message](../schema/metadata.md).

### Example

```py
from jcore_api import connect_local

conn = connect_local()

conn.get_metadata(['andysDevice.analog1', 'andysDevice.analog2'])
# returns {u'andysDevice.analog1': {u'units': u'V', u'max': 200, u'precision': 1, u'name': u'Analog 1', u'min': 0}, u'andysDevice.analog2': {u'units': u'V', u'max': 5, u'precision': 1, u'name': u'Analog 2', u'min': 0}}
```
