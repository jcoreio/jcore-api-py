# Exceptions

These exceptions may be thrown by JCore API calls if an error occurs.


### `JCoreAPIException`
The base class for JCore API exceptions.


### `JCoreAPIAuthException`
Will be raised if authentication fails or a JCore API request is made while the connection is not authenticated.


### `JCoreAPIErrorResponseException`
Will be raised if the server responds to a JCore API request with an error.


### `JCoreAPITimeoutException`
Will be raised if a JCore API request times out.


### `JCoreAPIConnectionClosedException`
Will be raised if a connection closes during a JCore API request or it was already closed before the request
was made.


### `JCoreAPIUnexpectedMessageException`
Will be raised if an unexpected message is received on the receive thread.


### `JCoreAPIInvalidMessageException`
Will be raised if the JCore API receives an invalid response.
