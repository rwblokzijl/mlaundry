from laundry.browser import encrypt_cookie, decrypt_cookie, get_last_used_profile
from laundry.browser import encode_cookie, decode_cookie

import unittest

class TestCookieCrypt(unittest.TestCase):
    def test_encode_then_decode_7char(self):
        value = "testtes"
        self.assertEqual( len(value), 7)
        encoded = encode_cookie(value)
        self.assertEqual( len(encoded), 16)
        self.assertEqual(
            decode_cookie(encoded),
            value
        )

    def test_encode_then_decode_15char(self):
        value = "testtesttesttes"
        self.assertEqual( len(value), 15)
        encoded = encode_cookie(value)
        self.assertEqual( len(encoded), 16)
        self.assertEqual(
            decode_cookie(encoded),
            value
        )

    def test_encode_then_decode_31char(self):
        value = "testtesttesttesttesttesttesttes"
        self.assertEqual( len(value), 31)
        encoded = encode_cookie(value)
        self.assertEqual( len(encoded), 32)
        self.assertEqual(
            decode_cookie(encoded),
            value
        )

    def test_encode_then_decode_32char(self):
        value = "testtesttesttesttesttesttesttest"
        self.assertEqual( len(value), 32)
        encoded = encode_cookie(value)
        self.assertEqual( len(encoded), 48)
        self.assertEqual(
            decode_cookie(encoded),
            value
        )

    def test_encrypt_then_decrypt(self):
        value = "testvalue"
        self.assertEqual(
            decrypt_cookie(encrypt_cookie(value)),
            value
        )

