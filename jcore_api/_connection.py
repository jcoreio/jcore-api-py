from __future__ import print_function
import json
import threading
import six
import time
import traceback
import sys

from ._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT
from .exceptions import JCoreAPIException, JCoreAPITimeoutException, JCoreAPIAuthException, \
                        JCoreAPIConnectionClosedException, JCoreAPIUnexpectedException, \
                        JCoreAPIServerException, JCoreAPIInvalidResponseException

def _defaultOnUnexpectedException(exc_info):
  print(*traceback.format_exception(*exc_info), file=sys.stderr)

def _wait(cv, timeout):
  startTime = time.time()
  cv.wait(timeout)
  if timeout and time.time() - startTime >= timeout:
    raise JCoreAPITimeoutException('operation timed out')

def _fromProtocolError(error):
  if error:
    if type(error) is six.text_type:
      return error
    if type(error) is dict:
      return error[six.u('error')] if six.u('error') in error else error

class Connection:
  """
  A connection a to jcore.io server.

  sock: the socket to communicate with.  It must have these methods
    send(message):  sends a message
    recv():         receives a message
    close():        closes the socket
  authRequired: whether authentication is required.
                If so, methods will throw an error if the client is not authenticated.
                default is True
  """
  def __init__(self, sock, authRequired=True, onUnexpectedException=_defaultOnUnexpectedException, defaultTimeout=None):
    self._lock = threading.RLock()
    self._sock = sock
    self._authRequired = authRequired
    self._onUnexpectedException = onUnexpectedException
    self._closed = False
    self._authenticating = False
    self._authenticated = False
    self._autherror = None
    self._authcv = threading.Condition(self._lock)
    self._defaultTimeout = defaultTimeout

    self._curMethodId = 0
    self._methodCalls = {}

    self._thread = threading.Thread(target=self._run, name="jcore.io Connection")
    self._thread.daemon = True
    self._thread.start()

  def _run(self):
    # store reference because this will be set to None upon close 
    sock = self._sock
    while not self._closed:
      self._onMessage(sock.recv())

  def authenticate(self, token, timeout=None):
    """
    authenticate the client.

    token: the token field from the decoded base64 api token.
    """
    assert type(token) is six.text_type and len(token) > 0, "token must be a non-empty unicode string"

    if timeout is None:
      timeout = self._defaultTimeout

    self._lock.acquire()
    try:
      if self._authenticated:
        raise JCoreAPIAuthException("already authenticated")
      if self._authenticating:
        raise JCoreAPIAuthException("authentication already in progress")

      self._authenticating = True
      self._autherror = None
    finally:
      self._lock.release()

    self._send(CONNECT, {six.u('token'): token})

    self._lock.acquire()
    try:
      while self._authenticating:
        _wait(self._authcv, timeout)

      if self._autherror:
        raise self._autherror
    finally:
      self._authenticating = False
      self._lock.release()

  def close(self, error=None):
    """
    Close this connection.

    error: the error to raise from all outstanding requests.
    """
    self._lock.acquire()
    try:
      if self._closed:
        return

      if self._authenticating:
        self._autherror = JCoreAPIConnectionClosedException("connection closed before auth completed", error)
        self._authcv.notify_all()

      for methodInfo in six.itervalues(self._methodCalls):
        methodInfo['error'] = JCoreAPIConnectionClosedException("connection closed", error)
        methodInfo['cv'].notify()

      self._methodCalls.clear()

      self._authenticating = False
      self._authenticated = False
      self._closed = True

      self._sock.close()
      self._sock = None

    finally:
      self._lock.release()

  def getRealTimeData(self, request=None, timeout=None):
    """
    Gets real-time data from the server.

    request: a dict that may contain a list of channelIds (strings).
             If channelIds are not given, gets all channels.

    returns TODO
    """
    if request:
      assert type(request) is dict, "request must be a dict if present"
      if ('channelIds' in request):
        assert type(request['channelIds']) is list, "channelIds must be a list if present"
    return self._call('getRealTimeData', [request] if request else [], timeout)

  def setRealTimeData(self, request, timeout=None):
    """
    Sets real-time data on the server.

    request: TODO
    """
    assert type(request) is dict, "request must be a dict"
    self._call('setRealTimeData', [request], timeout)

  def getMetadata(self, request=None, timeout=None):
    """
    Gets metadata from the server.

    request: a dict that may contain a list of channelIds (strings).
             If channelIds are not given, gets all channels.

    returns a dict mapping from channelId to dicts of min, max, name, and precision.
            all strings in the return value are unicode
    """
    if request:
      assert type(request) is dict, "request must be a dict if present"
      if ('channelIds' in request):
        assert type(request['channelIds']) is list, "channelIds must be a list if present"
    return self._call('getMetadata', [request] if request else [], timeout)

  def setMetadata(self, request, timeout=None):
    """
    Sets metadata on the server.

    request: TODO
    """
    assert type(request) is dict, "request must be a dict"
    self._call('setMetadata', [request], timeout)

  def _call(self, method, params, timeout=None):
    assert type(method) is str and len(method) > 0, "method must be a non-empty str"

    if timeout is None:
      timeout = self._defaultTimeout

    methodInfo = None

    self._lock.acquire()
    try:
      self._requireAuth()
      _id = str(self._curMethodId)
      self._curMethodId += 1
      methodInfo = {'cv': threading.Condition(self._lock)}
      self._methodCalls[_id] = methodInfo
    finally:
      self._lock.release()

    self._send(METHOD, {
      'id': _id,
      'method': method,
      'params': params 
    })

    self._lock.acquire()
    try:
      while not 'result' in methodInfo and not 'error' in methodInfo:
        _wait(methodInfo['cv'], timeout)
    finally:
      self._lock.release()

    if 'error' in methodInfo:
      raise methodInfo['error']
    return methodInfo['result']

  def _send(self, messageName, message):
    sock = None

    self._lock.acquire()
    try:
      sock = self._sock;
      if not sock or self._closed:
        raise JCoreAPIConnectionClosedException("connection closed")
    finally:
      self._lock.release()

    message['msg'] = messageName
    sock.send(json.dumps(message))

  def _onMessage(self, event):
    try:
      message = json.loads(event)
      if not six.u('msg') in message:
        raise JCoreAPIInvalidResponseException("msg field is missing", message)

      msg = message[six.u('msg')]
      if not (type(msg) is six.text_type and len(msg) > 0):
        raise JCoreAPIInvalidResponseException("msg must be a non-empty unicode string", message)

      self._lock.acquire()
      try:
        if self._closed:
          return

        if msg == CONNECTED:
          if not self._authenticating:
            raise JCoreAPIUnexpectedException("unexpected connected message", message)
          self._authenticating = False
          self._authenticated = True
          self._authcv.notify_all()

        elif msg == FAILED:
          errMsg = "authentication failed" if self._authenticating else "unexpected auth failed message"
          protocolError = _fromProtocolError(message[six.u('error')]) if six.u('error') in message else None
          self._authenticating = False
          self._authenticated = False
          self._autherror = JCoreAPIAuthException(errMsg + (": " + protocolError if protocolError else ""), message)
          self._authcv.notify_all()

        elif msg == RESULT:
          if not six.u('id') in message:
            raise JCoreAPIInvalidResponseException("id field is missing", message)
          _id = message[six.u('id')]
          if not (type(_id) is six.text_type and len(_id) > 0):
            raise JCoreAPIInvalidResponseException("id must be a non-empty unicode string", message)

          if not _id in self._methodCalls:
            raise JCoreAPIUnexpectedException("method call not found: " + _id, message)
            
          methodInfo = self._methodCalls[_id]
          del self._methodCalls[_id]

          if six.u('error') in message:
            methodInfo['error'] = JCoreAPIServerException(_fromProtocolError(message[six.u('error')]), message)
          elif six.u('result') in message:
            methodInfo['result'] = message[six.u('result')]
          else:
            methodInfo['error'] = JCoreAPIInvalidResponseException("message is missing result or error", message)
          methodInfo['cv'].notify()

        else:
          raise JCoreAPIInvalidResponseException("unknown message type: " + msg, message)
      finally:
        self._lock.release()
    except JCoreAPIException as e:
      try:
        self._onUnexpectedException(sys.exc_info())
      except Exception as e:
        traceback.print_exc()
    except Exception as e:
      try:
        self._onUnexpectedException((JCoreAPIUnexpectedException, JCoreAPIUnexpectedException("unexpected other exception", e), sys.exc_info()[2]))
      except Exception as e:
        traceback.print_exc()

  def _onClose(self, event):
    if not self._closed:
      self.close(JCoreAPIConnectionClosedException("connection closed: %(code), %(reason)" % event))

  def _requireAuth(self):
    self._lock.acquire()
    try:
      if self._closed:
        raise JCoreAPIConnectionClosedException("connection is already closed")
      if self._authenticating:
        raise JCoreAPIAuthException("authentication has not finished yet")
      if self._authRequired and not self._authenticated:
        raise JCoreAPIAuthException("not authenticated")
    finally:
      self._lock.release()
