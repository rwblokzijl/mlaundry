import unittest

from main import main

SLOW=True

class TestAcceptance(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skipUnless(SLOW, "slow")
    def test_get_laundry(self):
        disable_warnings(InsecureRequestWarning)
        main()

