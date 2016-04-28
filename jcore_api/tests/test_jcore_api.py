import six
import json
import threading
from unittest import TestCase

from jcore_api.protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT

if six.PY3:
  from queue import Queue
else:
  from Queue import Queue

import jcore_api

token = six.u("this is a test")

class MockSock:
  def __init__(self):
    self._sentQueue = Queue()
    self._recvQueue = Queue()
    self._closed = False

  def close(self):
    self.closed = True

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
  