# jcore-api-py

Python API for communicating with a jcore.io server.

## Requirements

Tested on CPython 2 and 3.

## Installation

```
pip install jcore_api
```

## Usage Example

```py
from jcore_api import connect

token = "eyJ1cmwiOiJ3czovL2xvY2FsaG9zdDozMDMwL2pjb3JlLWFwaSIsInRva2VuIjoiRWxsOGpBd1NRcGd4d2RidkJDSXo4dGZqL2VWSE9nWnV2RGFVM1JxM0tZRnFZaXVYeWZDa1VnbTlQbmVINHQ5aCJ9"

jcore = connect(token)

print(jcore.getMetadata())
```

## Reference

### connect(apiToken)

Connects to a jcore.io server and authenticates.

apiToken: an API token from the jcore.io server you wish to connect to.

returns: an authenticated Connection instance.

### Connection

#### getRealTimeData(request)

Gets real-time data from the server.

request: a dict that may contain a list of channelIds (strings).
         If channelIds are not given, gets all channels.

returns TODO

#### setRealTimeData(request)

Sets real-time data on the server.

request: TODO

#### getMetadata(request)

Gets metadata from the server.

request: a dict that may contain a list of channelIds (strings).
         If channelIds are not given, gets all channels.

returns a dict mapping from channelId to dicts of min, max, name, and precision.
        all strings in the return value are unicode

#### setMetadata(request)

Sets metadata on the server.

request: TODO
