from main import main, make_parser

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

import unittest

SLOW=True

class TestAcceptance(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

class TestParser(unittest.TestCase):

    def parse(self, string):
        return make_parser().parse_args(string.split())

    def test_parse_plain(self):
        args = self.parse("")
        print(args)

