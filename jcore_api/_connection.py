from __future__ import print_function
import json
import threading
import time
import traceback
import sys

import six

from ._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT, GET_HISTORICAL_DATA, \
    GET_METADATA, SET_METADATA, GET_REAL_TIME_DATA, SET_REAL_TIME_DATA
from .exceptions import JCoreAPIException, JCoreAPITimeoutException, JCoreAPIAuthException, \
    JCoreAPIConnectionClosedException, JCoreAPIUnexpectedMessageException, \
    JCoreAPIErrorResponseException, JCoreAPIInvalidMessageException

def _default_on_unexpected_exception(exc_info):
    print(*traceback.format_exception(*exc_info), file=sys.stderr)


def _wait(cv, timeout):
    startTime = time.time()
    cv.wait(timeout)
    if timeout and time.time() - startTime >= timeout:
        raise JCoreAPITimeoutException('operation timed out')


def _from_protocol_error(error):
    if error:
        if isinstance(error, six.text_type):
            return error
        if isinstance(error, dict):
            return error[six.u('error')] if six.u('error') in error else error

def _get_list(type_, items, name="items"):
    """
    Normalizes maybe item or list of items to maybe list
    """
    if isinstance(items, type_):
        return [items]
    if items:
        assert isinstance(items, list), name + " must be a " + type_ + " or list if present"
        for channelid in items:
            assert isinstance(channelid, type_), name + " must all be of type " + type_
    return items

def _get_channelids(channelids=None):
    return _get_list(six.string_types, channelids, name="channelids")

class JCoreAPIConnection:
    """
    A connection a to jcore.io server.

    sock: the socket to communicate with.    It must have these methods
        send(message):    sends a message
        recv():                 receives a message
        close():                closes the socket
    auth_required: whether authentication is required.
                                If so, methods will throw an error if the client is not authenticated.
                                default is True
    """
    def __init__(self, sock, auth_required=True, on_unexpected_exception=_default_on_unexpected_exception):
        self._lock = threading.RLock()
        self._sock = sock
        self._auth_required = auth_required
        self._on_unexpected_exception = on_unexpected_exception
        self._started = False
        self._closed = False
        self._authenticating = False
        self._authenticated = False
        self._autherror = None
        self._authcv = threading.Condition(self._lock)

        self._cur_method_id = 0
        self._method_calls = {}

        self._recv_thread = threading.Thread(
            target=self._run_recv_thread, name="jcore.io receiver")
        self._recv_thread.daemon = True

    def _run_recv_thread(self):
        # skip locking in this method since it's only reading fields
        sock = self._sock

        if not sock:
            return

        while not self._closed:
            try:
                self._handle_message(sock.recv())
            except JCoreAPITimeoutException:
                continue
            except JCoreAPIConnectionClosedException as error:
                self.close(error, sock_is_closed=True)
                return
            except Exception as e:
                try:
                    self._on_unexpected_exception(sys.exc_info())
                except Exception as e:
                    traceback.print_exc()

    def authenticate(self, token):
        """
        authenticate the client.

        token: the token field from the decoded base64 api token.
        """
        assert isinstance(token, six.text_type) and len(
            token) > 0, "token must be a non-empty unicode string"

        self._lock.acquire()
        try:
            if self._authenticated:
                raise JCoreAPIAuthException("already authenticated")
            if self._authenticating:
                raise JCoreAPIAuthException(
                    "authentication already in progress")

            self._authenticating = True
            self._autherror = None

            self._send(CONNECT, {six.u('token'): token})

            while self._authenticating:
                _wait(self._authcv, self._sock.gettimeout())

            if self._autherror:
                raise self._autherror
        finally:
            self._authenticating = False
            self._lock.release()
        
    def _require_auth(self):
        self._lock.acquire()
        try:
            if self._closed:
                raise JCoreAPIConnectionClosedException(
                    "connection is already closed")
            if self._authenticating:
                raise JCoreAPIAuthException(
                    "authentication has not finished yet")
            if self._auth_required and not self._authenticated:
                raise JCoreAPIAuthException("not authenticated")
        finally:
            self._lock.release()

    def close(self, error=JCoreAPIConnectionClosedException('connection closed'), sock_is_closed=False):
        """
        Close this connection.

        error: the error to raise from all outstanding requests.
        sock_is_closed: if True, will not redundantly call close() on the socket.
        """
        self._lock.acquire()
        try:
            if self._closed:
                return

            if self._authenticating:
                self._autherror = error
                self._authcv.notify_all()

            for method_call in six.itervalues(self._method_calls):
                method_call['error'] = error
                method_call['done'] = True
                method_call['cv'].notify()

            self._method_calls.clear()

            self._authenticating = False
            self._authenticated = False
            self._closed = True

            if not sock_is_closed:
                self._sock.close()
            self._sock = None

        finally:
            self._lock.release()

    def get_real_time_data(self, channelids=None):
        """
        Gets real-time data from the server.

        channelids: a string or list of strings specifying the channel id(s) to get data for

        returns: a JSON Real-Time Data object 
            (https://jcoreio.gitbooks.io/jcore-api-py/content/docs/api/schema/realTimeData.md)
        """
        return self._call(GET_REAL_TIME_DATA, [{'channelIds': _get_channelids(channelids)}] if channelids else [])

    def set_real_time_data(self, data):
        """
        Sets real-time data on the server.

        data: a dict mapping from channel id to value
        """
        assert isinstance(data, dict), "data must be a dict"
        self._call(SET_REAL_TIME_DATA, [data])

    def get_metadata(self, channelids=None):
        """
        Gets metadata from the server.

        channelids: a string or list of strings specifying the channel id(s) to get data for

        returns: a dict mapping from channel id to JSON Metadata object
            (https://jcoreio.gitbooks.io/jcore-api-py/content/docs/api/schema/metadata.md)
        """
        return self._call(GET_METADATA, [{'channelIds': _get_channelids(channelids)}] if channelids else [])

    def set_metadata(self, metadata):
        """
        Sets metadata on the server.

        metadata: a dict mapping from channel id to JSON Metadata object
        """
        assert isinstance(metadata, dict), "metadata must be a dict"
        self._call(SET_METADATA, [metadata])

    def get_historical_data(self, channelids, begintime, endtime):
        """
        Gets historical data from the server.

        channelids: a string or list of strings specifying the channel id(s) to get data for
        begintime: the beginning of the time range to fetch; either an ISO Date
                     string or a numeric timestamp (milliseconds since the epoch)
        endtime: the end of the time range to fetch; either an ISO Date
                   string or a numeric timestamp (milliseconds since the epoch)

        returns: a JSON Historical Data object
            (https://jcoreio.gitbooks.io/jcore-api-py/content/docs/api/schema/historicalData.md)
        """
        channelids = _get_channelids(channelids)
        assert isinstance(begintime, int) or isinstance(begintime, six.string_types), \
                "begintime must be a string or number"
        assert isinstance(endtime, int) or isinstance(endtime, six.string_types), \
                "endtime must be a string or number"
        return self._call(GET_HISTORICAL_DATA, [{'channelIds': channelids, 'beginTime': begintime, 'endTime': endtime}])

    def _call(self, method, params):
        assert isinstance(method, str) and len(
            method) > 0, "method must be a non-empty str"

        method_call = None
        _id = None

        self._lock.acquire()
        try:
            self._require_auth()
            _id = str(self._cur_method_id)
            self._cur_method_id += 1
            method_call = {
                'done': False,
                'error': None,
                'result': None,
                'cv': threading.Condition(self._lock) 
            }
            self._method_calls[_id] = method_call

            self._send(METHOD, {
                'id': _id,
                'method': method,
                'params': params
            })

            while not method_call['done']:
                _wait(method_call['cv'], self._sock.gettimeout())

            if method_call['error']:
                raise method_call['error']
            return method_call['result']
        finally:
            if _id in self._method_calls:
                del self._method_calls[_id]
            self._lock.release()

    def _send(self, message_name, message):
        sock = None

        self._lock.acquire()
        try:
            if not self._started:
                self._started = True
                self._recv_thread.start()

            sock = self._sock
            if not sock or self._closed:
                raise JCoreAPIConnectionClosedException("connection closed")
        finally:
            self._lock.release()

        message['msg'] = message_name
        sock.send(json.dumps(message))

    def _handle_message(self, event):
        message = json.loads(event)
        if six.u('msg') not in message:
            raise JCoreAPIInvalidMessageException(
                "msg field is missing", message)

        msg = message[six.u('msg')]
        if not (isinstance(msg, six.text_type) and len(msg) > 0):
            raise JCoreAPIInvalidMessageException(
                "msg must be a non-empty unicode string", message)

        # Synchronize all message handling to ensure we'll ignore messages
        # after the connection has closed
        self._lock.acquire()
        try:
            if self._closed:
                # don't raise an exception here, it has already been
                # handled in _run_recv_thread
                return

            if msg == CONNECTED:
                self._handle_connected_message(message)
            elif msg == FAILED:
                self._handle_failed_message(message)
            elif msg == RESULT:
                self._handle_result_message(message)
            else:
                self._handle_unknown_message(message)                 
        finally:
            self._lock.release()

    def _handle_connected_message(self, message):
        self._lock.acquire()
        try:
            if not self._authenticating:
                raise JCoreAPIUnexpectedMessageException(
                    "unexpected connected message", message)
            self._authenticating = False
            self._authenticated = True
            self._authcv.notify_all()
        finally:
            self._lock.release()

    def _handle_failed_message(self, message):
        self._lock.acquire()
        try:
            if not self._authenticating:
                raise JCoreAPIUnexpectedMessageException(
                    "unexpected auth failed message", message)
            error_msg = "authentication failed" if self._authenticating else "unexpected auth failed message"
            protocol_error = _from_protocol_error(
                message[six.u('error')]) if six.u('error') in message else None
            self._authenticating = False
            self._authenticated = False
            self._autherror = JCoreAPIAuthException(
                error_msg + (": " + protocol_error if protocol_error else ""), message)
            self._authcv.notify_all()
        finally:
            self._lock.release()

    def _handle_result_message(self, message):
        self._lock.acquire()
        try:
            msg = message[six.u('msg')]

            _id = message[six.u('id')]
            if not (isinstance(_id, six.text_type) and len(_id) > 0):
                raise JCoreAPIInvalidMessageException(
                    "id must be a non-empty unicode string", message)

            if _id not in self._method_calls:
                raise JCoreAPIUnexpectedMessageException(
                    "method call not found: " + _id, message)

            method_call = self._method_calls[_id]

            if six.u('error') in message:
                error = message[six.u('error')]
                if isinstance(error, JCoreAPIException):
                    method_call['error'] = error
                else:
                    method_call['error'] = JCoreAPIErrorResponseException(
                        _from_protocol_error(error), message)
            elif six.u('result') in message:
                method_call['result'] = message[six.u('result')]
            method_call['done'] = True
            method_call['cv'].notify()
        finally:
            self._lock.release()

    def _handle_unknown_message(self, message):
        msg = message[six.u('msg')]
        if six.u('id') not in message:
            if msg != RESULT:
                raise JCoreAPIInvalidMessageException(
                    'invalid message type: ' + msg, message)
            else:
                raise JCoreAPIInvalidMessageException(
                    "id field is missing", message)

        if six.u('error') not in message:
            message[six.u('error')] = JCoreAPIInvalidMessageException(
                'invalid message type: ' + msg, message)

        # handle it like a result message so that error gets raised on the
        # caller for its id
        return self._handle_result_message(message)
