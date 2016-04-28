import six
import json
import threading
from unittest import TestCase

if six.PY3:
  from queue import Queue
else:
  from Queue import Queue

import jcore_api

class TestSock:
  def __init__(self):
    self._sentQueue = Queue()
    self._recvQueue = Queue()
    self._closed = False

  def close(self):
    self.closed = True

  def send(self, message):
    self._sentQueue.put_nowait(message)

  def recv(self):
    return self._recvQueue.get()

class TestAPI(TestCase):
  def test_authenticate(self):
    sock = TestSock()
    conn = jcore_api.Connection(sock)

    token = six.u("this is a test")

    def runsock():
      message = json.loads(sock._sentQueue.get(timeout=1))
      self.assertEqual(message, {'msg': 'connect', 'token': token})
      sock._recvQueue.put_nowait(json.dumps({"msg": "connected"}))

    thread = threading.Thread(target=runsock)
    thread.daemon = True
    thread.start()

    conn.authenticate(token, timeout=3)

    self.assertFalse(conn._authenticating)
    self.assertTrue(conn._authenticated)

  def test_auth_failure(self):
    sock = TestSock()
    conn = jcore_api.Connection(sock)

    token = six.u("this is a test")

    def runsock():
      message = json.loads(sock._sentQueue.get(timeout=1))
      self.assertEqual(message, {'msg': 'connect', 'token': token})
      sock._recvQueue.put_nowait(json.dumps({"msg": "failed"}))

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
    sock = TestSock()
    conn = jcore_api.Connection(sock)

    token = six.u("this is a test")

    try:
      conn.authenticate(token, timeout=1)
      self.fail("authenticate should have timed out")
    except Exception as e:
      self.assertTrue("operation timed out" in e.args[0])

    self.assertFalse(conn._authenticating)
    self.assertFalse(conn._authenticated)

  def test_auth_while_authenticating_throws(self):
    sock = TestSock()
    conn = jcore_api.Connection(sock)

    token = six.u("this is a test")

    conn._authenticating = True

    try:
      conn.authenticate(token, timeout=1)
      self.fail("authenticate should have raised exception")
    except Exception as e:
      self.assertTrue("in progress" in e.args[0])

    self.assertTrue(conn._authenticating)
    self.assertFalse(conn._authenticated)

  def test_auth_while_authenticated_throws(self):
    sock = TestSock()
    conn = jcore_api.Connection(sock)

    token = six.u("this is a test")

    conn._authenticated = True

    try:
      conn.authenticate(token, timeout=1)
      self.fail("authenticate should have raised exception")
    except Exception as e:
      self.assertTrue("already authenticated" in e.args[0])

    self.assertFalse(conn._authenticating)
    self.assertTrue(conn._authenticated)
  