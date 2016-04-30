"""
A WebSocket-like interface to a unix socket with basic message framing
(from ._message_codec)
"""

import threading
from socket import socket

import six

if six.PY3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

from ..exceptions import JCoreAPIConnectionClosedException, JCoreAPITimeoutException
from ._message_codec import encode_message, MessageDecoder

CHUNK_SIZE = 2048

class JCoreUnixSocket:
    def __init__(self, sock):
        self._sock = sock
        self._recv_queue = Queue()
        self._started = False
        self._closed = False
        self._decoder = MessageDecoder(on_message=self._on_message)

        self._thread = threading.Thread(
            target=self._run, name="jcore.io unix socket")
        self._thread.daemon = True

    def _on_message(self, message):
        self._recv_queue.put_nowait(message)

    def _run(self):
        while not self._closed:
            try:
                message = self._sock.recv(CHUNK_SIZE)
            except socket.timeout:
                continue
            if not len(message):
                self._closed = True
                self._recv_queue.put_nowait(JCoreAPIConnectionClosedException("socket connection broken"))
                return
            self._decoder.decode(message)

    def gettimeout(self):
        return self._sock.gettimeout()

    def close(self):
        self._sock.close()
        self._closed = True

    def recv(self):
        if not self._started:
            self._started = True
            self._thread.start()

        try:
            message = self._recv_queue.get(timeout=self._sock.gettimeout())
        except Empty as e:
            raise JCoreAPITimeoutException("recv timed out", e)    
        if isinstance(message, Exception):
            # put exception back on the queue in case there are any
            # other waiting receivers
            self._recv_queue.put_nowait(message)
            raise message
        return message

    def send(self, message):
        totalsent = 0
        encoded = encode_message(message)
        while totalsent < len(encoded):
            try:
                sent = self._sock.send(encoded[totalsent:])
            except socket.timeout as e:
                raise JCoreAPITimeoutException("send timed out", e)
            if sent == 0:
                self._closed = True
                raise JCoreAPIConnectionClosedException("socket connection broken")
            totalsent += sent
