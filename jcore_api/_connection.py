from __future__ import print_function
import json
import threading
import time
import traceback
import sys

import six

from ._protocol import CONNECT, CONNECTED, FAILED, METHOD, RESULT, \
    GET_METADATA, SET_METADATA, GET_REAL_TIME_DATA, SET_REAL_TIME_DATA
from .exceptions import JCoreAPIException, JCoreAPITimeoutException, JCoreAPIAuthException, \
    JCoreAPIConnectionClosedException, JCoreAPIUnexpectedException, \
    JCoreAPIServerException, JCoreAPIInvalidResponseException


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

    def __init__(self, sock, auth_required=True, on_unexpected_exception=_default_on_unexpected_exception, default_timeout=None):
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
        self._default_timeout = default_timeout

        self._cur_method_id = 0
        self._method_calls = {}

        self._thread = threading.Thread(
            target=self._run, name="jcore.io Connection")
        self._thread.daemon = True

    def _run(self):
        # store reference because this will be set to None upon close
        sock = self._sock
        while not self._closed:
            try:
                message = sock.recv()
            except JCoreAPIConnectionClosedException as error:
                self.close(error, sock_is_closed=True)
                return
            self._on_message(message)

    def authenticate(self, token, timeout=None):
        """
        authenticate the client.

        token: the token field from the decoded base64 api token.
        """
        assert isinstance(token, six.text_type) and len(
            token) > 0, "token must be a non-empty unicode string"

        if timeout is None:
            timeout = self._default_timeout

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
                _wait(self._authcv, timeout)

            if self._autherror:
                raise self._autherror
        finally:
            self._authenticating = False
            self._lock.release()

    def close(self, error=JCoreAPIConnectionClosedException('connection closed'), sock_is_closed=False):
        """
        Close this connection.

        error: the error to raise (wrapped in a JCoreAPIConnectionClosedException) 
               from all outstanding requests.
        sock_is_closed: if True, will not redundantly call close() on the socket.
        """
        self._lock.acquire()
        try:
            if self._closed:
                return

            if self._authenticating:
                self._autherror = error
                self._authcv.notify_all()

            for method_info in six.itervalues(self._method_calls):
                method_info['error'] = error
                method_info['cv'].notify()

            self._method_calls.clear()

            self._authenticating = False
            self._authenticated = False
            self._closed = True

            if not sock_is_closed:
                self._sock.close()
            self._sock = None

        finally:
            self._lock.release()

    def get_real_time_data(self, request=None, timeout=None):
        """
        Gets real-time data from the server.

        request: a dict that may contain a list of channelIds (strings).
                         If channelIds are not given, gets all channels.

        returns TODO
        """
        if request:
            assert isinstance(
                request, dict), "request must be a dict if present"
            if 'channelIds' in request:
                assert isinstance(
                    request['channelIds'], list), "channelIds must be a list if present"
        return self._call(GET_REAL_TIME_DATA, [request] if request else [], timeout)

    def set_real_time_data(self, request, timeout=None):
        """
        Sets real-time data on the server.

        request: TODO
        """
        assert isinstance(request, dict), "request must be a dict"
        self._call(SET_REAL_TIME_DATA, [request], timeout)

    def get_metadata(self, request=None, timeout=None):
        """
        Gets metadata from the server.

        request: a dict that may contain a list of channelIds (strings).
                         If channelIds are not given, gets all channels.

        returns a dict mapping from channelId to dicts of min, max, name, and precision.
                        all strings in the return value are unicode
        """
        if request:
            assert isinstance(
                request, dict), "request must be a dict if present"
            if 'channelIds' in request:
                assert isinstance(
                    request['channelIds'], list), "channelIds must be a list if present"
        return self._call(GET_METADATA, [request] if request else [], timeout)

    def set_metadata(self, request, timeout=None):
        """
        Sets metadata on the server.

        request: TODO
        """
        assert isinstance(request, dict), "request must be a dict"
        self._call(SET_METADATA, [request], timeout)

    def _call(self, method, params, timeout=None):
        assert isinstance(method, str) and len(
            method) > 0, "method must be a non-empty str"

        if timeout is None:
            timeout = self._default_timeout

        method_info = None

        self._lock.acquire()
        try:
            self._require_auth()
            _id = str(self._cur_method_id)
            self._cur_method_id += 1
            method_info = {'cv': threading.Condition(self._lock)}
            self._method_calls[_id] = method_info
        finally:
            self._lock.release()

        self._send(METHOD, {
            'id': _id,
            'method': method,
            'params': params
        })

        self._lock.acquire()
        try:
            while 'result' not in method_info and 'error' not in method_info:
                _wait(method_info['cv'], timeout)
        finally:
            self._lock.release()

        if 'error' in method_info:
            raise method_info['error']
        return method_info['result']

    def _send(self, message_name, message):
        sock = None

        self._lock.acquire()
        try:
            if not self._started:
                self._started = True
                self._thread.start()

            sock = self._sock
            if not sock or self._closed:
                raise JCoreAPIConnectionClosedException("connection closed")
        finally:
            self._lock.release()

        message['msg'] = message_name
        sock.send(json.dumps(message))

    def _on_message(self, event):
        try:
            message = json.loads(event)
            if six.u('msg') not in message:
                raise JCoreAPIInvalidResponseException(
                    "msg field is missing", message)

            msg = message[six.u('msg')]
            if not (isinstance(msg, six.text_type) and len(msg) > 0):
                raise JCoreAPIInvalidResponseException(
                    "msg must be a non-empty unicode string", message)

            self._lock.acquire()
            try:
                if self._closed:
                    return

                if msg == CONNECTED:
                    if not self._authenticating:
                        raise JCoreAPIUnexpectedException(
                            "unexpected connected message", message)
                    self._authenticating = False
                    self._authenticated = True
                    self._authcv.notify_all()

                elif msg == FAILED:
                    error_msg = "authentication failed" if self._authenticating else "unexpected auth failed message"
                    protocol_error = _from_protocol_error(
                        message[six.u('error')]) if six.u('error') in message else None
                    self._authenticating = False
                    self._authenticated = False
                    self._autherror = JCoreAPIAuthException(
                        error_msg + (": " + protocol_error if protocol_error else ""), message)
                    self._authcv.notify_all()

                elif msg == RESULT:
                    if six.u('id') not in message:
                        raise JCoreAPIInvalidResponseException(
                            "id field is missing", message)
                    _id = message[six.u('id')]
                    if not (isinstance(_id, six.text_type) and len(_id) > 0):
                        raise JCoreAPIInvalidResponseException(
                            "id must be a non-empty unicode string", message)

                    if _id not in self._method_calls:
                        raise JCoreAPIUnexpectedException(
                            "method call not found: " + _id, message)

                    method_info = self._method_calls[_id]
                    del self._method_calls[_id]

                    if six.u('error') in message:
                        method_info['error'] = JCoreAPIServerException(
                            _from_protocol_error(message[six.u('error')]), message)
                    elif six.u('result') in message:
                        method_info['result'] = message[six.u('result')]
                    else:
                        method_info['error'] = JCoreAPIInvalidResponseException(
                            "message is missing result or error", message)
                    method_info['cv'].notify()

                else:
                    raise JCoreAPIInvalidResponseException(
                        "unknown message type: " + msg, message)
            finally:
                self._lock.release()
        except JCoreAPIException as e:
            try:
                self._on_unexpected_exception(sys.exc_info())
            except Exception as e:
                traceback.print_exc()
        except Exception as e:
            try:
                self._on_unexpected_exception((JCoreAPIUnexpectedException, JCoreAPIUnexpectedException(
                    "unexpected other exception", e), sys.exc_info()[2]))
            except Exception as e:
                traceback.print_exc()

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
