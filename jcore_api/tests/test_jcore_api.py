import json
import threading
import traceback
import time
from unittest import TestCase

import six

if six.PY3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

from jcore_api._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT, \
    GET_METADATA, SET_METADATA, GET_REAL_TIME_DATA, SET_REAL_TIME_DATA, GET_HISTORICAL_DATA
from jcore_api import JCoreAPIConnection
from jcore_api.exceptions import JCoreAPIAuthException, JCoreAPITimeoutException, \
    JCoreAPIConnectionClosedException, JCoreAPIErrorResponseException, \
    JCoreAPIInvalidMessageException

token = six.u("this is a test")

def swallow_exception(exc_info):
    pass


class MockSock:
    def __init__(self, autorespond=False):
        self.sent_queue = Queue()
        self.recv_queue = Queue()
        self.closed = False
        self.timeout = 0.5
        self.autorespond = autorespond

    def gettimeout(self):
        return self.timeout 

    def close(self):
        self.closed = True

    def send(self, message):
        parsed = json.loads(message)
        self.sent_queue.put_nowait(parsed)
        if self.autorespond:
            self.recv_queue.put_nowait({'msg': RESULT, 'id': parsed['id']})

    def recv(self):
        try:
            message = self.recv_queue.get(timeout=self.timeout)
        except Empty as e:
            raise JCoreAPITimeoutException("recv timed out", e) 

        if isinstance(message, Exception):
            raise message
        return json.dumps(message)

class TestAPI(TestCase):
    def test_authenticate(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': CONNECT, 'token': token})
            sock.recv_queue.put_nowait({"msg": CONNECTED})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        conn.authenticate(token)

        self.assertFalse(conn._authenticating)
        self.assertTrue(conn._authenticated)

        thread.join(1)

    def test_auth_failure(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': CONNECT, 'token': token})
            sock.recv_queue.put_nowait({"msg": FAILED})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.authenticate(token)
            self.fail("authenticate should have raised exception")
        except JCoreAPIAuthException as e:
            pass
        finally:
            thread.join(1)

        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_auth_timeout(self):
        sock = MockSock()
        sock.timeout = 0.01
        conn = JCoreAPIConnection(sock)

        try:
            conn.authenticate(token)
            self.fail("authenticate should have timed out")
        except JCoreAPITimeoutException as e:
            pass

        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_auth_while_authenticating(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._authenticating = True

        try:
            conn.authenticate(token)
            self.fail("authenticate should have raised exception")
        except JCoreAPIAuthException as e:
            pass

        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_auth_while_authenticated(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        try:
            conn.authenticate(token)
            self.fail("authenticate should have raised exception")
        except JCoreAPIAuthException as e:
            pass

        self.assertFalse(conn._authenticating)
        self.assertTrue(conn._authenticated)

    def test_auth_already_closed(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._closed = True

        try:
            conn.authenticate(token)
            self.fail("authenticate should have raised exception")
        except JCoreAPIConnectionClosedException:
            pass

        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_auth_connection_closed(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        exception = JCoreAPIConnectionClosedException('test')

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': CONNECT, 'token': token})
            sock.recv_queue.put_nowait(exception)

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.authenticate(token)
            self.fail("authenticate should have raised exception")
        except JCoreAPIConnectionClosedException as e:
            self.assertIs(exception, e)

        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)
        self.assertTrue(conn._closed)

        thread.join(1)

    def test_call(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        result1 = {'hello': 'world'}
        result2 = {'cats': 'dogs'}

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': METHOD, 'id': '0',    'method': GET_METADATA, 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '0', 'result': result1})
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': METHOD, 'id': '1',    'method': GET_METADATA, 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '1', 'result': result2})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        self.assertEqual(conn.get_metadata(), result1)
        self.assertEqual(conn.get_metadata(), result2)

        thread.join(1)

    def test_get_metadata_schema(self):
        sock = MockSock(autorespond=True)
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        conn.get_metadata()
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_METADATA),
                six.u('params'): [],
                six.u('id'): six.u('0')
            }, sock.sent_queue.get(timeout=sock.timeout))

        conn.get_metadata(channelids='hello')
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_METADATA),
                six.u('params'): [{six.u('channelIds'): [six.u('hello')]}],
                six.u('id'): six.u('1')
            }, sock.sent_queue.get(timeout=sock.timeout))

        conn.get_metadata(channelids=['hello', 'world'])
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_METADATA),
                six.u('params'): [{six.u('channelIds'): [six.u('hello'), six.u('world')]}],
                six.u('id'): six.u('2')
            }, sock.sent_queue.get(timeout=sock.timeout))

    def test_set_metadata_schema(self):
        sock = MockSock(autorespond=True)
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        conn.set_metadata({'hello': {'name': 'szia'}})
        self.assertEqual({
                six.u('msg'): 'method',
                six.u('method'): six.u(SET_METADATA),
                six.u('params'): [
                    {six.u('hello'): {six.u('name'): six.u('szia')}}
                ],
                six.u('id'): six.u('0')
            }, sock.sent_queue.get(timeout=sock.timeout))

    def test_get_real_time_data_schema(self):
        sock = MockSock(autorespond=True)
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        conn.get_real_time_data()
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_REAL_TIME_DATA),
                six.u('params'): [],
                six.u('id'): six.u('0')
            }, sock.sent_queue.get(timeout=sock.timeout))

        conn.get_real_time_data(channelids='hello')
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_REAL_TIME_DATA),
                six.u('params'): [{six.u('channelIds'): [six.u('hello')]}],
                six.u('id'): six.u('1')
            }, sock.sent_queue.get(timeout=sock.timeout))

        conn.get_real_time_data(channelids=['hello', 'world'])
        self.assertEqual({
                six.u('msg'): 'method', 
                six.u('method'): six.u(GET_REAL_TIME_DATA),
                six.u('params'): [{six.u('channelIds'): [six.u('hello'), six.u('world')]}],
                six.u('id'): six.u('2')
            }, sock.sent_queue.get(timeout=sock.timeout))

    def test_set_real_time_data_schema(self):
        sock = MockSock(autorespond=True)
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        conn.set_real_time_data({'powerlevel': 9000.000001})
        self.assertEqual({
                six.u('msg'): 'method',
                six.u('method'): six.u(SET_REAL_TIME_DATA),
                six.u('params'): [
                    {six.u('powerlevel'): 9000.000001}
                ],
                six.u('id'): six.u('0')
            }, sock.sent_queue.get(timeout=sock.timeout))

    def test_get_historical_data_schema(self):
        sock = MockSock(autorespond=True)
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        conn.get_historical_data(channelids='channel1', begintime=10000, endtime=20000)
        self.assertEqual({
                six.u('msg'): 'method',
                six.u('method'): six.u(GET_HISTORICAL_DATA),
                six.u('params'): [{
                    six.u('channelIds'): [six.u('channel1')],
                    six.u('beginTime'): 10000,
                    six.u('endTime'): 20000
                }],
                six.u('id'): six.u('0')
            }, sock.sent_queue.get(timeout=sock.timeout))

    def test_call_error(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': METHOD, 'id': '0',    'method': GET_METADATA, 'params': []})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': '0', 'error': 'test_call_error'})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.get_metadata()
            self.fail("get_metadata should have raised an exception")
        except JCoreAPIErrorResponseException as e:
            self.assertTrue('test_call_error' in e.args[0])
            pass
        finally:
            thread.join(timeout=sock.timeout)

    def test_call_invalid_responses(self):
        sock = MockSock()
        conn = JCoreAPIConnection(
            sock, on_unexpected_exception=swallow_exception)

        conn._authenticated = True

        result1 = {'hello': 'world'}

        def runsock():
            self.assertEqual(sock.sent_queue.get(timeout=sock.timeout), {
                             'msg': METHOD, 'id': '0',    'method': GET_METADATA, 'params': []})
            sock.recv_queue.put_nowait({'id': '0', 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": None, 'id': '0', 'result': result1})
            sock.recv_queue.put_nowait({"msg": RESULT, 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": RESULT, 'id': None, 'result': result1})
            sock.recv_queue.put_nowait(
                {"msg": "wtf is this?", 'id': '0', 'result': result1})

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.get_metadata()
            self.fail("get_metadata should have raised exception")
        except JCoreAPIInvalidMessageException:
            pass
        finally:
            thread.join(timeout=sock.timeout)

    def test_call_unauthenticated(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        try:
            conn.get_metadata()
            self.fail("get_metadata should have raised exception")
        except JCoreAPIAuthException:
            pass


    def test_call_connection_closed(self):
        sock = MockSock()
        conn = JCoreAPIConnection(
            sock, on_unexpected_exception=swallow_exception)

        conn._authenticated = True

        exception = JCoreAPIConnectionClosedException("test")

        def runsock():
            sock.recv_queue.put_nowait(exception)

        thread = threading.Thread(target=runsock)
        thread.daemon = True
        thread.start()

        try:
            conn.get_metadata()
            self.fail("get_metadata should have raised exception")
        except JCoreAPIConnectionClosedException:
            pass
        finally:
            thread.join(1)

        self.assertEqual(conn._closed, True)
        self.assertEqual(conn._authenticated, False)
        self.assertEqual(conn._authenticating, False)

    def test_call_already_closed(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._closed = True

        try:
            conn.get_metadata()
            self.fail("get_metadata should have raised exception")
        except JCoreAPIConnectionClosedException:
            pass

    def test_call_timeout(self):
        sock = MockSock()
        conn = JCoreAPIConnection(
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
            self.assertEqual(conn.get_metadata(), result)
            self.fail("get_metadata should have raised exception")
        except JCoreAPITimeoutException:
            pass
        finally:
            thread.join(1)

    def test_close(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn.close()

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)

    def test_close_during_auth(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        def runauth():
            try:
                conn.authenticate(token)
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
        thread.join(timeout=sock.timeout)

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)
        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)

    def test_close_during_call(self):
        sock = MockSock()
        conn = JCoreAPIConnection(sock)

        conn._authenticated = True

        def runcall():
            try:
                conn.get_metadata()
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
        thread.join(timeout=sock.timeout)

        self.assertTrue(conn._closed)
        self.assertTrue(sock.closed)
        self.assertFalse(conn._authenticating)
        self.assertFalse(conn._authenticated)
