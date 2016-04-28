import json
import threading
import traceback
import time
from unittest import TestCase

import six

if six.PY3:
    from queue import Queue
else:
    from Queue import Queue

from jcore_api._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT
import jcore_api
from jcore_api.exceptions import JCoreAPIAuthException, JCoreAPITimeoutException, \
    JCoreAPIConnectionClosedException, JCoreAPIServerException, \
    JCoreAPIInvalidResponseException

token = six.u("this is a test")


def swallow_exception(exc_info):
    pass


class MockSock:
    def __init__(self):
        self.sent_queue = Queue()
        self.recv_queue = Queue()
        self.closed = False

    def close(self):
        self.closed = True

    def send(self, message):
        self.sent_queue.put_nowait(json.loads(message))

    def recv(self):
        return json.dumps(self.recv_queue.get())


class TestAPI(TestCase):

    def test_authenticate(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': CONNECT, 'token': token})
            sock.recv_queue.put_nowait({"msg": CONNECTED})

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
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': CONNECT, 'token': token})
            sock.recv_queue.put_nowait({"msg": FAILED})

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

    def test_auth_while_authenticating(self):
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

    def test_auth_while_authenticated(self):
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
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': METHOD, 'id': '0',    'method': 'get_metadata', 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '0', 'result': result1})
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': METHOD, 'id': '1',    'method': 'get_metadata', 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '1', 'result': result2})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        self.assertEqual(conn.get_metadata(timeout=1), result1)
        self.assertEqual(conn.get_metadata(timeout=1), result2)

    def test_call_error(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        conn._authenticated = True

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': METHOD, 'id': '0',    'method': 'get_metadata', 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '0', 'error': 'test_call_error'})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.get_metadata(timeout=1)
            self.fail("get_metadata should have raised an exception")
        except JCoreAPIServerException as e:
            self.assertTrue('test_call_error' in e.args[0])
            pass
        finally:
            thread.join(timeout=3)

    def test_call_invalid_responses(self):
        sock = MockSock()
        conn = jcore_api.Connection(
            sock, on_unexpected_exception=swallow_exception)

        conn._authenticated = True

        result1 = {'hello': 'world'}

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=1), {
                             'msg': METHOD, 'id': '0',    'method': 'get_metadata', 'params': []})
            sock.recv_queue.put_nowait({'id': '0', 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": None, 'id': '0', 'result': result1})
            sock.recv_queue.put_nowait({"msg": RESULT, 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': None, 'result': result1})
            sock.recv_queue.put_nowait({"msg": RESULT, 'id': '0'})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '0', 'result': None})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '1', 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": "wtf is this?", 'id': '0', 'result': result1})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.get_metadata(timeout=1)
            self.fail("get_metadata should have raised exception")
        except JCoreAPIInvalidResponseException:
            pass
        finally:
            thread.join(timeout=3)

    def test_call_unauthenticated(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        try:
            conn.get_metadata(timeout=1)
            self.fail("get_metadata should have raised exception")
        except JCoreAPIAuthException:
            pass

    def test_call_closed(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        conn._closed = True

        try:
            conn.get_metadata(timeout=1)
            self.fail("get_metadata should have raised exception")
        except JCoreAPIConnectionClosedException:
            pass

    def test_call_timeout(self):
        sock = MockSock()
        conn = jcore_api.Connection(
            sock, on_unexpected_exception=swallow_exception)

        conn._authenticated = True

        result = {'hello': 'world'}

        def runsock():
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '1', 'result': result})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            self.assertEqual(conn.get_metadata(timeout=1), result)
            self.fail("get_metadata should have raised exception")
        except JCoreAPITimeoutException:
            pass

    def test_close(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        conn.close()

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)

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
                self.fail(
                    "authenticate should have raised JCoreAPIConnectionClosedException")

        thread = threading.Thread(target=runauth)
        thread.daemon = True
        thread.start()

        # wait for authenticate to begin
        # since it's a blocking call, I'm not sure how exactly to wait for it
        # to begin
        time.sleep(0.1)

        conn.close()
        thread.join(timeout=2)

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)
        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_close_during_call(self):
        sock = MockSock()
        conn = jcore_api.Connection(sock)

        conn._authenticated = True

        def runcall():
            try:
                conn.get_metadata(timeout=1)
                self.fail("get_metadata should have raised exception")
            except JCoreAPIConnectionClosedException:
                pass
            except:
                traceback.print_exc()
                self.fail(
                    "get_metadata should have raised JCoreAPIConnectionClosedException")

        thread = threading.Thread(target=runcall)
        thread.daemon = True
        thread.start()

        # wait for get_metadata to begin
        # since it's a blocking call, I'm not sure how exactly to wait for it
        # to begin
        time.sleep(0.1)

        conn.close()
        thread.join(timeout=2)

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)
        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)
