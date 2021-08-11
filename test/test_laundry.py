import unittest

from laundry.laundry import *

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

class TestUtil(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_time(self):
        disable_warnings(InsecureRequestWarning)
        users = list(get_users())
        time = get_time(users[0])
        print(time)

