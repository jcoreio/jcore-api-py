class JCoreAPIException(Exception):
    """
    base class for JCore API exceptions.
    """
    pass


class JCoreAPIErrorResponseException(JCoreAPIException):
    """
    Will be raised if the server responds to a JCore API request with an error.
    """
    pass


class JCoreAPITimeoutException(JCoreAPIException):
    """
    Will be raised if a JCore API request times out.
    """
    pass


class JCoreAPIConnectionClosedException(JCoreAPIException):
    """
    Will be raised if a connection closes during a JCore API request or it was already closed before the request
    was made.
    """
    pass


class JCoreAPIAuthException(JCoreAPIException):
    """
    Will be raised if authentication fails or a JCore API request is made while the connection is not authenticated.
    """
    pass


class JCoreAPIUnexpectedMessageException(JCoreAPIException):
    """
    Will be raised if an unexpected message is received on the receive thread.
    """
    pass


class JCoreAPIInvalidMessageException(JCoreAPIException):
    """
    Will be raised if the JCore API receives an invalid response.
    """
    pass
