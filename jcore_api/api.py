import websocket
from base64 import b64decode
import json

from .api_common import LOCAL_SOCKET_PATH
from .connection import Connection

def connect(apiToken):
    """Connects to a jcore.io server.
    """
    assert type(apiToken) is str or type(apiToken) is unicode, 'apiToken must be a base64-encoded string or unicode'
    assert len(apiToken) > 0, 'len(apiToken) must be > 0'

    parsed = json.loads(b64decode(apiToken))
    print(parsed)
    assert type(parsed) is dict, 'decoded apiToken must be a dict'

    url, token = parsed[u'url'], parsed[u'token']
    assert type(url) is unicode, 'decoded url must be a unicode'
    assert len(url) > 0, "len(<decoded apiToken>['url']) must be > 0"
    assert type(token) is unicode, 'decoded token must be a unicode'
    assert len(token) > 0, "len(<decoded apiToken>['token']) must be > 0"

    sock = websocket.create_connection(url)

    connection = Connection(sock)
    connection.authenticate(token)

    return connection
