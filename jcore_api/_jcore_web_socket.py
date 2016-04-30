from websocket import WebSocket
from websocket._exceptions import WebSocketConnectionClosedException, WebSocketTimeoutException

from .exceptions import JCoreAPIConnectionClosedException, JCoreAPITimeoutException

class JCoreWebSocket:
    def __init__(self, sock):
        self._sock = sock

    def gettimeout(self):
        return self._sock.gettimeout()

    def close(self):
        self._sock.close()

    def recv(self):
        try:
            return self._sock.recv()
        except WebSocketConnectionClosedException as e:
            raise JCoreAPIConnectionClosedException("connection closed", e)
        except WebSocketTimeoutException as e:
            raise JCoreAPITimeoutException("recv timed out", e)

    def send(self, data):
        try:
            return self._sock.send(data)
        except WebSocketConnectionClosedException as e:
            raise JCoreAPIConnectionClosedException("connection closed", e)
        except WebSocketTimeoutException as e:
            raise JCoreAPITimeoutException("send timed out", e)
