# `get_real_time_data([request])`

Gets the latest values of channel(s).

### Arguments

1. [`request`] *(dict)*: request options, including:
  * [`'channelIds'`] *(list)*: list of channel ids (strings) to get data for (defaults to all channels)

### Returns

*(dict)*: a parsed [JSON Real-Time Data message](../schema/realTimeData.md).

### Example

```py
from jcore_api import connect_local

conn = connect_local()

conn.get_real_time_data({'channelIds': ['andysDevice.analog1', 'andysDevice.analog2']})
# {u'timestamp': u'2016-05-02T20:52:38.455Z', u'data': {u'andysDevice.analog1': 0.568205191, u'andysDevice.analog2': 0.9166735450000001}}
```
