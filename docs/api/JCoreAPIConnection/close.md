# `close([error], [sock_is_closed])`

Closes the connection.  Any outstanding method calls will throw the given (or default) error.

### Arguments

1. [`error`] *(Exception)*: the reason the connection closed.
2. [`sock_is_closed`] *(bool)*: if `True`, don't try to close the underlying socket.
  Otherwise, try to close it.
