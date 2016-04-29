from websocket import WebSocket
from websocket._exceptions import WebSocketConnectionClosedException

from .exceptions import JCoreAPIConnectionClosedException

class JCoreWebSocket(WebSocket):
    def recv_frame(self):
        try:
            return WebSocket.recv_frame(self)
        except WebSocketConnectionClosedException as e:
            raise JCoreAPIConnectionClosedException("connection closed", e)

    def send_frame(self, frame):
        try:
            return WebSocket.send_frame(self, frame)
        except WebSocketConnectionClosedException as e:
            raise JCoreAPIConnectionClosedException("connection closed", e)
