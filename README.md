# jcore-api-py

Python API for communicating with a jcore.io server.

## Compatibility

This package is known to require at least Python 2.6 as it uses `bytearray`.

Tested on CPython 2.7.11 and 3.5.1.

## Installation

```
pip install jcore_api
```

## Usage Example

```py
from jcore_api import connect

token = "eyJ1cmwiOiJ3czovL2xvY2FsaG9zdDozMDMwL2pjb3JlLWFwaSIsInRva2VuIjoiRWxsOGpBd1NRcGd4d2RidkJDSXo4dGZqL2VWSE9nWnV2RGFVM1JxM0tZRnFZaXVYeWZDa1VnbTlQbmVINHQ5aCJ9"

jcore = connect(token)

print(jcore.get_metadata())
```

## Reference

### connect(api_token)

Connects to a jcore.io server and authenticates.

api_token: an API token from the jcore.io server you wish to connect to.

returns: an authenticated Connection instance.

### Connection

#### get_real_time_data(request)

Gets real-time data from the server.

request: a dict that may contain a list of channelIds (strings).
         If channelIds are not given, gets all channels.

returns TODO

#### set_real_time_data(request)

Sets real-time data on the server.

request: TODO

#### get_metadata(request)

Gets metadata from the server.

request: a dict that may contain a list of channelIds (strings).
         If channelIds are not given, gets all channels.

returns a dict mapping from channelId to dicts of min, max, name, and precision.
        all strings in the return value are unicode

#### set_metadata(request)

Sets metadata on the server.

request: TODO

### get_historical_data(request)

Gets historical data from the server.

request: a dict with the following fields:
* channelIds: a list of channel ids
* beginTime: the beginning of the time range to fetch; either an ISO Date
            string or a numeric timestamp (milliseconds since the epoch)
* endTime: the end of the time range to fetch; either an ISO Date
            string or a numeric timestamp (milliseconds since the epoch)

returns: a dict with the following fields (unicode keys):
* beginTime: the beginning of the result time range: milliseconds since the epoch
* endTime: the beginning of the result time range: milliseconds since the epoch
* data: TODO
