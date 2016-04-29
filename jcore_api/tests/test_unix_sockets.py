"""
tests for _unix_sockets subpackage
"""

import random
import string
from unittest import TestCase

import six

if six.PY3:
    from queue import Queue
else:
    from Queue import Queue

from jcore_api._unix_sockets._message_codec import encode_message, MessageDecoder
from jcore_api._unix_sockets._jcore_unix_socket import JCoreUnixSocket

def _random_string(length):
    return six.u(''.join(random.choice(string.ascii_uppercase) for
                    _ in range(length)))

def _join_bytearrays(bytearrays):
    total_bytes = 0
    for array in bytearrays:
        total_bytes += len(array)
    result = bytearray(total_bytes)
    begin = 0
    for array in bytearrays:
        end = begin + len(array)
        result[begin:end] = array
        begin = end
    return result

def _chunk_bytearray(array, chunk_length):
    result = []
    begin = 0
    while begin < len(array):
        end = min(begin + chunk_length, len(array))
        result.append(array[begin:end])
        begin = end
    return result

class MockSock:
    def __init__(self):
        self.sent_queue = Queue()
        self.recv_queue = Queue()
        self.closed = False

    def close(self):
        self.closed = True

    def send(self, message):
        self.sent_queue.put_nowait(message)

    def recv(self):
        message = self.recv_queue.get()
        if isinstance(message, Exception):
            raise message
        return message

class TestMessageCodec(TestCase):
    def test_encode_decode(self):
        expected_messages = []
        actual_messages = []
        encoded_messages = []
        def on_message(message):
            actual_messages.append(message) 

        # generate a bunch of messages of varying length
        for _ in range(50):
            message = _random_string(random.randint(10, 100))
            expected_messages.append(message)
            encoded_messages.append(encode_message(message))

        # concatenate all of the encoded messages

        all_bytes = _join_bytearrays(encoded_messages)

        decoder = MessageDecoder(on_message)

        def test_chunk_size(size):
            """
            tests that the messages can be successfully decoded when the bytes
            are split up into chunks of the given size
            """
            del actual_messages[:]

            for chunk in _chunk_bytearray(all_bytes, size):
                decoder.decode(six.binary_type(chunk))

            self.assertEqual(expected_messages, actual_messages)

        test_chunk_size(1)
        test_chunk_size(10)
        test_chunk_size(100)
        test_chunk_size(496)
        test_chunk_size(10000)

class TestUnixSocket(TestCase):
    def test_receive(self):
        sock = MockSock()
        unixSock = JCoreUnixSocket(sock)

        expected_messages = []
        encoded_messages = []
        actual_messages = []

        # generate a bunch of messages of varying length
        for _ in range(50):
            message = _random_string(random.randint(10, 100))
            expected_messages.append(message)
            encoded_messages.append(encode_message(message))

        # concatenate all of the encoded messages

        all_bytes = _join_bytearrays(encoded_messages)

        def test_chunk_size(size):
            """
            tests that the messages can be successfully decoded when the bytes
            are split up into chunks of the given size
            """
            del actual_messages[:]

            for chunk in _chunk_bytearray(all_bytes, size):
                sock.recv_queue.put_nowait(six.binary_type(chunk))

            for _ in range(len(expected_messages)):
                actual_messages.append(unixSock.recv())

            self.assertEqual(expected_messages, actual_messages)

        test_chunk_size(1)
        test_chunk_size(10)
        test_chunk_size(100)
        test_chunk_size(496)
        test_chunk_size(10000)


