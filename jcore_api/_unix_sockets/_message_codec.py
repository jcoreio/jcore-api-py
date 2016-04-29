"""
utils for framing string messages for unix sockets
"""

import struct

import six

PREAMBLE = 35    # '#' character
LENGTH_LEN = 4  # number of bytes for representing message length
HEADER_LEN = 1 + LENGTH_LEN  # number of bytes in message header

DECODE_STATE_INITIAL = 0
DECODE_STATE_READ_LENGTH = 1
DECODE_STATE_READ_DATA = 2


def encode_message(data):
    """
    frames a message for sending on a unix socket

    data: the data to encode, a string
    """

    assert isinstance(data, six.string_types)

    encoded_data = data.encode('utf8')
    encoded = bytearray(len(encoded_data) + HEADER_LEN)
    pos = 0
    encoded[0] = PREAMBLE
    pos += 1
    encoded[pos:pos + LENGTH_LEN] = struct.pack(">I", len(data))
    pos += LENGTH_LEN
    encoded[pos:] = encoded_data
    return six.binary_type(encoded)

class MessageDecoder:
    """
    decodes framed messages received from the unix socket.

    on_message: callback to call with decoded message(s) when complete
                frames have been received
    """
    def __init__(self, on_message):
        assert hasattr(on_message, '__call__'), "on_message must be callable"
        self._on_message = on_message
        self._decode_state = DECODE_STATE_INITIAL
        self._length_buf = bytearray(LENGTH_LEN)
        self._length_buf_pos = 0
        self._decode_buffer_pos = 0
        self._decode_buffer = None

    def decode(self, src_buffer):
        """
        decode a chunk of data from the unix socket.

        src_buffer: the data from the unix socket, a byte array or binary string
        """

        if isinstance(src_buffer, six.binary_type):
            src_buffer = bytearray(src_buffer)

        src_pos = 0
        while src_pos < len(src_buffer):
            src_remain = len(src_buffer) - src_pos
            bytes_read = 0

            if self._decode_state is DECODE_STATE_INITIAL:
                preamble = src_buffer[src_pos]
                bytes_read = 1
                assert preamble is PREAMBLE, "preamble does not match; expected %(exp)c, got %(actual)c" % \
                    {'exp': PREAMBLE, 'actual': preamble}
                self._decode_state = DECODE_STATE_READ_LENGTH

            elif self._decode_state is DECODE_STATE_READ_LENGTH:
                bytes_read = min(src_remain, LENGTH_LEN - self._length_buf_pos)
                self._length_buf[self._length_buf_pos:self._length_buf_pos + bytes_read] = \
                    src_buffer[src_pos:src_pos + bytes_read]
                self._length_buf_pos += bytes_read
                if self._length_buf_pos >= LENGTH_LEN:
                    message_length = struct.unpack(">I", self._length_buf[0:LENGTH_LEN])[0]
                    if message_length:
                        self._decode_buffer = bytearray(message_length)
                        self._decode_buffer_pos = 0
                        self._decode_state = DECODE_STATE_READ_DATA
                    else:
                        self._on_message(six.u(''))
                        self._decode_state = DECODE_STATE_INITIAL
                    self._length_buf_pos = 0
                    self._length_buf = bytearray(LENGTH_LEN)

            elif self._decode_state is DECODE_STATE_READ_DATA:
                bytes_read = min(src_remain, 
                    len(self._decode_buffer) - self._decode_buffer_pos)
                self._decode_buffer[self._decode_buffer_pos:self._decode_buffer_pos + bytes_read] = \
                    src_buffer[src_pos:src_pos + bytes_read]
                self._decode_buffer_pos += bytes_read
                if self._decode_buffer_pos >= len(self._decode_buffer):
                    self._on_message(self._decode_buffer.decode('utf8'))
                    self._decode_state = DECODE_STATE_INITIAL
                    self._decode_buffer = None

            assert bytes_read > 0
            src_pos += bytes_read
