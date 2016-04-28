class JCoreAPIException(Exception):
    """
    base class for JCore API exceptions.
    """
    pass


class JCoreAPIServerException(JCoreAPIException):
    """
    Will be raised if the server responds to a request with an error.
    """
    pass


class JCoreAPITimeoutException(JCoreAPIException):
    """
    Will be raised if a JCore API request times out.
    """
    pass


class JCoreAPIConnectionClosedException(JCoreAPIException):
    """
    Will be raised if a JCore API request is made while the connection is closed.
    """
    pass


class JCoreAPIAuthException(JCoreAPIException):
    """
    Will be raised if a JCore API request is made while the connection is not authorized.
    """
    pass


class JCoreAPIUnexpectedException(JCoreAPIException):
    """
    Will be raised if an unexpected exception is raised or unexpected message is received
    on the receive thread.
    """
    pass


class JCoreAPIInvalidResponseException(JCoreAPIException):
    """
    Will be raised if an invalid response is received by the JCore API.
    """
    pass
