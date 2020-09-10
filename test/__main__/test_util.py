from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

import unittest

import util

class TestUtil(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_time(self):
        disable_warnings(InsecureRequestWarning)

        users = util.get_users()
        username = next(iter(users))
        passw = users[username]

        time = util.get_time(username, passw)
        print(time)


