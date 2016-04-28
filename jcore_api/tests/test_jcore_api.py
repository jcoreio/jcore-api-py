import six
import json
import threading
import traceback
from unittest import TestCase

if six.PY3:
  from queue import Queue
else:
  from Queue import Queue

from jcore_api._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT
import jcore_api
from jcore_api._exceptions import JCoreAPIAuthException, JCoreAPITimeoutException, \
                                  JCoreAPIConnectionClosedException

token = six.u("this is a test")

class MockSock:
  def __init__(self):
    self._sentQueue = Queue()
    self._recvQueue = Queue()
    self._closed = False

  def close(self):
    self._closed = True

  def send(self, message):
    self._sentQueue.put_nowait(json.loads(message))

  def recv(self):
    return json.dumps(self._recvQueue.get())

class TestAPI(TestCase):
  def test_authenticate(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    def runsock():
      self.assertEqual(sock._sentQueue.get(timeout=1), {'msg': CONNECT, 'token': token})
      sock._recvQueue.put_nowait({"msg": CONNECTED})

    thread = threading.Thread(target=runsock)
    thread.daemon = True
    thread.start()

    conn.authenticate(token, timeout=3)

    self.assertFalse(conn._authenticating)
    self.assertTrue(conn._authenticated)

  def test_auth_failure(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    def runsock():
      self.assertEqual(sock._sentQueue.get(timeout=1), {'msg': CONNECT, 'token': token})
      sock._recvQueue.put_nowait({"msg": FAILED})

    thread = threading.Thread(target=runsock)
    thread.daemon = True
    thread.start()

    try:
      conn.authenticate(token, timeout=3)
      self.fail("authenticate should have raised exception")
    except Exception as e:
      self.assertTrue("authentication failed" in e.args[0])

    self.assertFalse(conn._authenticating)
    self.assertFalse(conn._authenticated)

  def test_auth_timeout(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    try:
      conn.authenticate(token, timeout=0.1)
      self.fail("authenticate should have timed out")
    except Exception as e:
      self.assertTrue("operation timed out" in e.args[0])

    self.assertFalse(conn._authenticating)
    self.assertFalse(conn._authenticated)

  def test_auth_while_authenticating_throws(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._authenticating = True

    try:
      conn.authenticate(token, timeout=1)
      self.fail("authenticate should have raised exception")
    except Exception as e:
      self.assertTrue("in progress" in e.args[0])

    self.assertTrue(conn._authenticating)
    self.assertFalse(conn._authenticated)

  def test_auth_while_authenticated_throws(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._authenticated = True

    try:
      conn.authenticate(token, timeout=1)
      self.fail("authenticate should have raised exception")
    except Exception as e:
      self.assertTrue("already authenticated" in e.args[0])

    self.assertFalse(conn._authenticating)
    self.assertTrue(conn._authenticated)
  
  def test_call(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._authenticated = True

    result1 = {'hello': 'world'}
    result2 = {'cats': 'dogs'}

    def runsock():
      self.assertEqual(sock._sentQueue.get(timeout=1), {'msg': METHOD, 'id': '0',  'method': 'getMetadata', 'params': []})
      sock._recvQueue.put_nowait({"msg": RESULT, 'id': '0', 'result': result1})
      self.assertEqual(sock._sentQueue.get(timeout=1), {'msg': METHOD, 'id': '1',  'method': 'getMetadata', 'params': []})
      sock._recvQueue.put_nowait({"msg": RESULT, 'id': '1', 'result': result2})

    thread = threading.Thread(target=runsock)
    thread.daemon = True
    thread.start()

    self.assertEqual(conn.getMetadata(timeout=1), result1)
    self.assertEqual(conn.getMetadata(timeout=1), result2)

  def test_call_unauthenticated(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    try:
      conn.getMetadata(timeout=1)
      self.fail("getMetadata should have raised exception")
    except JCoreAPIAuthException as e:
      pass
  
  def test_call_closed(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._closed = True

    try:
      conn.getMetadata(timeout=1)
      self.fail("getMetadata should have raised exception")
    except JCoreAPIConnectionClosedException:
      pass

  def test_call_timeout(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._authenticated = True

    result = {'hello': 'world'}

    def runsock():
      sock._recvQueue.put_nowait({"msg": RESULT, 'id': '1', 'result': result})

    thread = threading.Thread(target=runsock)
    thread.daemon = True
    thread.start()

    try:
      self.assertEqual(conn.getMetadata(timeout=1), result)
      self.fail("getMetadata should have raised exception")
    except JCoreAPITimeoutException:
      pass

  def test_close(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn.close()

    self.assertTrue(conn._closed)
    self.assertTrue(sock._closed)

  def test_close_during_auth(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    def runauth():
      try:
        conn.authenticate(token, timeout=5)
        self.fail("authenticate should have raised exception")
      except JCoreAPIConnectionClosedException:
        pass
      except:
        traceback.print_exc()
        self.fail("authenticate should have raised JCoreAPIConnectionClosedException")

    thread = threading.Thread(target=runauth)
    thread.daemon = True
    thread.start()

    conn.close()
    thread.join(timeout=1)

    self.assertTrue(conn._closed)
    self.assertTrue(sock._closed)
    self.assertFalse(conn._authenticating)
    self.assertFalse(conn._authenticated)
  
  def test_close_during_call(self):
    sock = MockSock()
    conn = jcore_api.Connection(sock)

    conn._authenticated = True

    def runcall():
      try:
        conn.getMetadata(timeout=1)
        self.fail("getMetadata should have raised exception")
      except JCoreAPIConnectionClosedException:
        pass
      except:
        traceback.print_exc()
        self.fail("getMetadata should have raised JCoreAPIConnectionClosedException")

    thread = threading.Thread(target=runcall)
    thread.daemon = True
    thread.start()

    conn.close()
    thread.join(timeout=1)

    self.assertTrue(conn._closed)
    self.assertTrue(sock._closed)
    self.assertFalse(conn._authenticating)
    self.assertFalse(conn._authenticated)
 