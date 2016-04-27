import websocket
import six
import json
from base64 import b64decode

from .api_common import LOCAL_SOCKET_PATH
from .connection import Connection

def connect(apiToken):
    """
    Connects to a jcore.io server and authenticates.

    apiToken: an API token from the jcore.io server you wish to connect to.

    returns: an authenticated Connection instance.
    """
    assert type(apiToken) is str or type(apiToken) is six.text_type, 'apiToken must be a base64-encoded string'
    assert len(apiToken) > 0, 'len(apiToken) must be > 0'

    parsed = json.loads(b64decode(six.b(apiToken)).decode('utf8'))
    assert type(parsed) is dict, 'decoded apiToken must be a dict'

    url, token = parsed[u'url'], parsed[u'token']
    assert type(url) is six.text_type, 'decoded url must be a unicode string'
    assert len(url) > 0, "len(<decoded apiToken>['url']) must be > 0"
    assert type(token) is six.text_type, 'decoded token must be a unicode string'
    assert len(token) > 0, "len(<decoded apiToken>['token']) must be > 0"

    sock = websocket.create_connection(url)

    connection = Connection(sock)
    connection.authenticate(token)

    return connection
