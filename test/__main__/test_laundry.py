from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

import unittest
import util
import laundry

disable_warnings(InsecureRequestWarning)

class TestAcceptance(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_availability(self):

        users = laundry.get_users()
        username = next(iter(users))
        passw = users[username]

        bookings = util.get_all_bookings(users)
        print(bookings)
