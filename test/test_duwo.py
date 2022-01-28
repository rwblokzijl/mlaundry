from laundry.duwo import _parse_datetime

import unittest

from datetime import datetime

class TestParsingOfDateWithMissingYear(unittest.TestCase):

    """Test case docstring."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_current_year(self):
        now = datetime(2021, 8, 14, 17, 50)
        date = "12-08 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year
                )

    def test_last_year(self):
        now = datetime(2021, 3, 11, 17, 50)
        date = "11-12 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year-1
                )

    def test_next_year(self):
        now = datetime(2021, 11, 11, 17, 50)
        date = "11-01 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year+1
                )

    def test_bare_difference_last_year(self):
        now = datetime(2021, 6, 30, 17, 50)
        date = "31-12 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year-1
                )

    def test_bare_difference_current(self):
        now = datetime(2021, 7, 2, 17, 50)
        date = "31-12 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year
                )
