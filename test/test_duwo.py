from laundry.duwo import _parse_datetime, Duwo
from laundry.duwo import write_to_file, read_from_file, get_cached
from main import get_all_users
import unittest
import shutil
from unittest.mock import Mock

from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

import os
from pathlib import Path

from typing import *

from datetime import datetime

class TestParsingOfDateWithMissingYear(unittest.TestCase):

    """Test case docstring."""

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

class TestPersistence(unittest.TestCase):
    """Test case docstring."""

    filepath = Path("./testdata/test1")

    def tearDown(self):
        try:
            shutil.rmtree(self.filepath.parents[0])
        except FileNotFoundError:
            pass

    def test_read_not_exists(self):
        self.assertEqual(
            read_from_file("./this_file_does_not_exist"),
            None
        )

    def test_write(self):
        testdata = """This is
        some multiline
        testdata"""

        write_to_file(filepath=self.filepath, data=testdata)
        self.assertEqual(
            read_from_file(self.filepath),
            testdata
        )

    def test_unpersisted_call_count(self):
        func = Mock(return_value="test")
        get_cached(self.filepath, func)
        self.assertTrue(func.called)

    def test_persisted_call_count(self):
        func = Mock(return_value="test")
        get_cached(self.filepath, func)
        get_cached(self.filepath, func)
        self.assertEqual(func.call_count, 1)

    def test_persisted_call_result(self):
        func = Mock(return_value="test")
        data1 = get_cached(self.filepath, func)
        data2 = get_cached(self.filepath, func)
        self.assertEqual(func.call_count, 1)
        self.assertEqual(data1, func())
        self.assertEqual(data2, func())

    def test_cached_none(self):
        pass

class TestDuwoLogin(unittest.TestCase):

    duwo_session_path = Path("./test_duwocache")
    def setUp(self):
        os.makedirs(self.duwo_session_path, exist_ok=True)

    def tearDown(self):
        try:
            shutil.rmtree(self.duwo_session_path)
        except FileNotFoundError:
            pass

    def test_load_same_user(self):
        users = get_all_users()
        duwo1 = Duwo(user = users[0], cache_dir=self.duwo_session_path)
        duwo2 = Duwo(user = users[0], cache_dir=self.duwo_session_path)
        self.assertEqual(
            duwo1._get_session(),
            duwo2._get_session()
        )

    def test_get_different_users(self):
        users = get_all_users()
        duwo1 = Duwo(users[0], cache_dir=self.duwo_session_path)
        duwo2 = Duwo(users[1], cache_dir=self.duwo_session_path)
        self.assertNotEqual(
            duwo1._get_session(),
            duwo2._get_session()
        )

class TestDuwo(unittest.TestCase):

    duwo_session_path = Path("./testsessions")
    call_cache_dir = Path("./call_cache")

    # def tearDown(self):
    #     shutil.rmtree(self.duwo_session_path)

    def setUp(self):
        users = get_all_users()
        self.duwo = Duwo(users[0], cache_dir=self.duwo_session_path)

    def call_with_cache(self, url):
        return

    def test_reservations(self):
        # parse reservations
        # get reservations
        pass


