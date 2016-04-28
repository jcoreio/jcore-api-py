class JCoreAPIException(Exception):
  pass

class JCoreAPIServerException(JCoreAPIException):
  pass

class JCoreAPITimeoutException(JCoreAPIException):
  pass

class JCoreAPIConnectionClosedException(JCoreAPIException):
  pass

class JCoreAPIAuthException(JCoreAPIException):
  pass

class JCoreAPIUnexpectedException(JCoreAPIException):
  pass
