import json
from base64 import b64decode
import socket

import six

from websocket import WebSocket

from ._api_common import LOCAL_SOCKET_PATH
from ._connection import JCoreAPIConnection
from ._jcore_web_socket import JCoreWebSocket
from ._unix_sockets._jcore_unix_socket import JCoreUnixSocket

def _default_create_web_socket(url):
    sock = WebSocket()
    sock.connect(url)
    return sock

def connect(api_token, create_socket=_default_create_web_socket, **kwargs):
    """
    Connects to a jcore.io server and authenticates.

    api_token: an API token from the jcore.io server you wish to connect to.

    returns: an authenticated JCoreAPIConnection instance.
    """
    assert isinstance(api_token, six.string_types) and len(api_token) > 0, \
        'api_token must be a nonempty string'

    parsed = json.loads(b64decode(six.b(api_token)).decode('utf8'))
    assert isinstance(parsed, dict), 'decoded api_token must be a dict'

    url, token = parsed[u'url'], parsed[u'token']
    assert isinstance(url, six.string_types) and len(
        url) > 0, 'decoded url must be a nonempty string'
    assert isinstance(token, six.string_types) and len(
        token) > 0, 'decoded token must be a nonempty string'

    sock = JCoreWebSocket(create_socket(url))
    connection = JCoreAPIConnection(sock, **kwargs)
    connection.authenticate(token)
    return connection

def _default_create_unix_socket(path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    return sock

def connect_local(create_socket=_default_create_unix_socket, **kwargs):
    """
    Connects to a jcore.io server on the local machine via a
    unix socket.

    returns: an JCoreAPIConnection instance.
    """
    sock = JCoreUnixSocket(create_socket(LOCAL_SOCKET_PATH))
    return JCoreAPIConnection(sock, auth_required=False, **kwargs)
