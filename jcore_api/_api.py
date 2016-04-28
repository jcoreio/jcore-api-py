import json
from base64 import b64decode

import six
import websocket

from ._api_common import LOCAL_SOCKET_PATH
from ._connection import Connection


def connect(api_token):
    """
    Connects to a jcore.io server and authenticates.

    api_token: an API token from the jcore.io server you wish to connect to.

    returns: an authenticated Connection instance.
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

    sock = websocket.create_connection(url)

    connection = Connection(sock)
    connection.authenticate(token)

    return connection
