"""
tests for _unix_sockets subpackage
"""

import six
from unittest import TestCase

from jcore_api._unix_sockets._message_codec import encode_message, MessageDecoder

class TestMessageCodec(TestCase):
    def test_encode_decode(self):
        def on_message(message):
            self.assertEqual(message, 'lorem ipsum dolor sit amet')

        decoder = MessageDecoder()
        frame = encode_message('lorem ipsum dolor sit amet')

        decoder.decode(frame, on_message)

        # test all possible versions of the message split into two
        for i in range(len(frame)):
          decoder.decode(frame[:i], on_message)
          decoder.decode(frame[i:], on_message)
