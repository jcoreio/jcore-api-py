import json
import threading
import six

CONNECT = six.u('connect')
CONNECTED = six.u('connected')
FAILED = six.u('failed')
METHOD = six.u('method')
RESULT = six.u('result')

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
  def __init__(self, sock, authRequired=True):
    self._lock = threading.RLock()
    self._sock = sock
    self._authRequired = authRequired
    self._closed = False
    self._authenticating = False
    self._authenticated = False
    self._autherror = None
    self._authcv = threading.Condition(self._lock)

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

  def authenticate(self, token):
    """
    authenticate the client.

    token: the token field from the decoded base64 api token.
    """
    assert type(token) is six.text_type and len(token) > 0, "token must be a non-empty unicode string"

    self._lock.acquire()
    try:
      if self._authenticated:
        raise RuntimeError("already authenticated")
      if self._authenticating:
        raise RuntimeError("authentication already in progress")

      self._authenticating = True
      self._autherror = None
    finally:
      self._lock.release()

    self._send(CONNECT, {six.u('token'): token})

    self._lock.acquire()
    try:
      while not self._authenticated and not self._autherror:
        self._authcv.wait()

      if self._autherror:
        raise self._autherror
    finally:
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
        self._autherror = error or RuntimeError("connection closed before auth completed")
        self._authcv.notify_all()

      for id, methodInfo in self._methodCalls:
        methodInfo['error'] = error or RuntimeError("connection closed")
        methodInfo['cv'].notify()

      self._methodCalls.clear()

      self._authenticating = False
      self._authenticated = False
      self._closed = True

      self._sock.close()
      self._sock = None

    finally:
      self._lock.release()

  def getRealTimeData(self, request=None):
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
    return self._call('getRealTimeData', request)

  def setRealTimeData(self, request):
    """
    Sets real-time data on the server.

    request: TODO
    """
    assert type(request) is dict, "request must be a dict"
    self._call('setRealTimeData', request)

  def getMetadata(self, request=None):
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
    return self._call('getMetadata', request)

  def setMetadata(self, request):
    """
    Sets metadata on the server.

    request: TODO
    """
    assert type(request) is dict, "request must be a dict"
    self._call('setMetadata', request)

  def _call(self, method, *params):
    assert type(method) is str and len(method) > 0, "method must be a non-empty str"

    methodInfo = None

    self._lock.acquire()
    try:
      self._requireAuth()
      id = str(++self._curMethodId)
      methodInfo = {'cv': threading.Condition(self._lock)}
      self._methodCalls[id] = methodInfo
    finally:
      self._lock.release()

    self._send(METHOD, {
      'id': id,
      'method': method,
      'params': params 
    })

    self._lock.acquire()
    try:
      while not 'result' in methodInfo and not 'error' in methodInfo:
        methodInfo['cv'].wait()
    finally:
      self._lock.release()

    if 'error' in methodInfo:
      raise methodInfo['error']
    return methodInfo['result']

  def _send(self, messageName, message):
    message['msg'] = messageName
    sock = self._sock;
    if not sock:
      raise RuntimeError("connection is already closed")
    sock.send(json.dumps(message))

  def _onMessage(self, event):
    message = json.loads(event)
    msg = message[six.u('msg')]
    assert type(msg) is six.text_type and len(msg) > 0, "msg must be a non-empty unicode string"

    self._lock.acquire()
    try:
      if self._closed:
        return

      if msg == CONNECTED:
        if not self._authenticating:
          raise RuntimeError("unexpected connected message")
        self._authenticating = False
        self._authenticated = True
        self._authcv.notify_all()

      elif msg == FAILED:
        errMsg = "authentication failed" if self._authenticating else "unexpected auth failed message"
        protocolError = _fromProtocolError(message[six.u('error')])
        self._authenticating = False
        self._authenticated = False
        self._autherror = RuntimeError(errMsg + (": " + protocolError if protocolError else ""))
        self._authcv.notify_all()

      elif msg == RESULT:
        id = message[six.u('id')]
        assert type(id) is six.text_type and len(id) > 0, "id must be a non-empty unicode string"

        methodInfo = self._methodCalls[id]
        del self._methodCalls[id]
        if not methodInfo:
          raise RuntimeError("method call not found: " + id)

        if six.u('error') in message:
          methodInfo['error'] = _fromProtocolError(message[six.u('error')])
        else:
          methodInfo['result'] = message[six.u('result')]
        methodInfo['cv'].notify()

      else:
        raise RuntimeError("unexpected message: " + msg)
    finally:
      self._lock.release()

  def _onClose(self, event):
    if not self._closed:
      self.close(RuntimeError("connection closed: %(code), %(reason)" % event))

  def _requireAuth(self):
    self._lock.acquire()
    try:
      if self._closed:
        raise RuntimeError("connection is already closed")
      if self._authenticating:
        raise RuntimeError("authentication has not finished yet")
      if self._authRequired and not self._authenticated:
        raise RuntimeError("not authenticated")
    finally:
      self._lock.release()

def _fromProtocolError(error):
  errMsg = None
  if error:
    errMsg = error['error'] if 'error' in error else error
  return errMsg if ((type(errMsg) is str or type(errMsg) is unicode) and len(errMsg)) else None
