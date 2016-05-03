# `get_metadata([request])`

### Arguments

1. [`request`] *(dict)*: request options, including:
  * [`'channelIds'`] *(list)*: list of channel ids (strings) to get data for (defaults to all channels)

### Returns

*(dict)*: A parsed [JSON Metadata message](../schema/metadata.md).

### Example

```py
from jcore_api import connect_local

conn = connect_local()

conn.get_metadata({'channelIds': ['andysDevice.analog1', 'andysDevice.analog2']})
# {u'andysDevice.analog1': {u'units': u'V', u'max': 200, u'precision': 1, u'name': u'Analog 1', u'min': 0}, u'andysDevice.analog2': {u'units': u'V', u'max': 5, u'precision': 1, u'name': u'Analog 2', u'min': 0}}
```
