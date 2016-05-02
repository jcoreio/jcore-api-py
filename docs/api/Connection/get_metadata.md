# `get_metadata([request])`

### Arguments

1. [`request`] *(dict)*: request options, including:
  * [`'channelIds'`] *(list)*: list of channel ids (strings) to get data for (defaults to all channels)

### Returns

*(dict)*: a mapping from channelId (string) to metadata for that channel, a *(dict)* containing:
  * [`'name'`] *(string)*: the channel's display name
  * [`'min'`] *(float)*: lower bound of the display range
  * [`'max'`] *(float)*: upper bound of the display range
  * [`'units'`] *(string)*: what units the channel values are in
  * [`'precision'`]: *(float)*: display precision.  Should be an unsigned int, but is `float` because it
    comes from JSON.

### Example

```py
from jcore_api import connect

conn = connect("eyJ1cmwiOiJ3czovL2xvY2FsaG9zdDozMDMwL2pjb3JlLWFwaSIsInRva2VuIjoiRWpITEkvcFlpOWxrbldUL2E5dEJnNlY2Um9pdXhsTEZJOUdMTUJUYk9oQm15bko1ZFlGRGZWRVJ3YnJmUlFWcSJ9")

conn.get_metadata({'channelIds': ['andysDevice.analog1', 'andysDevice.analog2']})
# {u'andysDevice.analog1': {u'units': u'V', u'max': 200, u'precision': 1, u'name': u'Analog 1', u'min': 0}, u'andysDevice.analog2': {u'units': u'V', u'max': 5, u'precision': 1, u'name': u'Analog 2', u'min': 0}}
```