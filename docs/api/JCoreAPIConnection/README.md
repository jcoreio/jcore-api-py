# `JCoreAPIConnection`

This class represents a connection to the server and allows you to call API methods.

### Methods

* [get_metadata([request])](get_metadata.md): Gets metadata about channel(s), for instance the name and units
* [set_metadata(metadata)](set_metadata.md): Sets metadata about channel(s), for instance the name and units
* [get_real_time_data([request])](get_real_time_data.md): Gets the latest values of channel(s)
* [set_real_time_data(data)](set_real_time_data.md): Sets the values of channel(s)
* [get_historical_data(request)](get_historical_data_md): Gets the latest values of channel(s)
* [close([error], [sock_is_closed])](close.md): Closes the connection
