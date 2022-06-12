from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from laundry.duwo import _parse_datetime, Duwo, User, MachineType
from laundry.duwo import write_to_file, read_from_file, get_cached
from laundry.duwo import ReservaionTimeSlot
from main import get_all_users

import unittest

from unittest.mock import Mock
from parameterized import parameterized

import datetime
import os
import shutil

from typing import *
from pathlib import Path

SKIP_ALL=False # If true skip all slow tests
RUN_ALL=False # If true run all tests
SKIP_CONNECT = (SKIP_ALL or True and not RUN_ALL, "Tests that use the network are skipped")
SKIP_SLEEP   = (SKIP_ALL or True and not RUN_ALL, "Tests that have a time.sleep are skipped")

class TestParsingOfDateWithMissingYear(unittest.TestCase):

    """Test case docstring."""

    def test_current_year(self):
        now = datetime.datetime(2021, 8, 14, 17, 50)
        date = "12-08 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year
                )

    def test_last_year(self):
        now = datetime.datetime(2021, 3, 11, 17, 50)
        date = "11-12 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year-1
                )

    def test_next_year(self):
        now = datetime.datetime(2021, 11, 11, 17, 50)
        date = "11-01 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year+1
                )

    def test_bare_difference_last_year(self):
        now = datetime.datetime(2021, 6, 30, 17, 50)
        date = "31-12 23:40"

        dt = _parse_datetime(date, now)

        self.assertEqual(
                dt.year,
                now.year-1
                )

    def test_bare_difference_current(self):
        now = datetime.datetime(2021, 7, 2, 17, 50)
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

    @unittest.skipIf(*SKIP_CONNECT)
    def test_load_same_user(self):
        users = get_all_users()
        duwo1 = Duwo(user = users[0], session_cache_dir=self.duwo_session_path).login()
        duwo2 = Duwo(user = users[0], session_cache_dir=self.duwo_session_path).login()
        self.assertEqual(
            duwo1._get_session(),
            duwo2._get_session()
        )

    @unittest.skipIf(*SKIP_CONNECT)
    def test_get_different_users(self):
        users = get_all_users()
        duwo1 = Duwo(users[0], session_cache_dir=self.duwo_session_path).login()
        duwo2 = Duwo(users[1], session_cache_dir=self.duwo_session_path).login()
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
        self.duwo = Duwo(users[0], session_cache_dir=self.duwo_session_path)

    def call_with_cache(self, url):
        return

class TestBookings(unittest.TestCase):
    @parameterized.expand( [
        ["washer1", 59, 45, MachineType.WASHER],
        ["washer2", 35, 45, MachineType.WASHER],
        ["washer3", 56, 45, MachineType.WASHER],
        ["washer4", 60, 45, MachineType.WASHER],

        ["dryer1", 40, 35, MachineType.DRYER],
        ["dryer2", 45, 35, MachineType.DRYER],
        ["dryer3", 50, 35, MachineType.DRYER],
        ["dryer4", 57, 35, MachineType.DRYER],
        ["dryer5", 59, 35, MachineType.DRYER],
        ["dryer6", 80, 70, MachineType.DRYER],
        ["dryer7", 120, 105, MachineType.DRYER],
    ])
    def test_get_time_delta_washers(self, name, a, b, mtype):
        test_user = User(
            email = "test",
            passw = "test"
        )
        self.assertEqual(
            Duwo(test_user, load_session=False)._get_actual_timedelta(
                datetime.timedelta(minutes=a),
                mtype=mtype),
            datetime.timedelta(minutes=b)
        )

class TestCallCache(unittest.TestCase):
    duwo_session_path = Path("./testsessions")
    call_cache_dir    = Path("./test_call_cache")

    def setUp(self):
        os.makedirs(self.call_cache_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.call_cache_dir, ignore_errors=True)


    @unittest.skipIf(*SKIP_SLEEP)
    def test_cache_is_reused(self):
        from time import sleep
        """
        MachineAvailability.php includes a timestamp with 1 second granularity
        """
        users = get_all_users()

        first = Duwo(users[0],
                     session_cache_dir=self.duwo_session_path,
                     call_cache_dir=self.call_cache_dir
                     ).login(
                     ).get_page("https://duwo.multiposs.nl/MachineAvailability.php")

        from bs4 import BeautifulSoup
        self.assertEqual(
            str(first),
            str(BeautifulSoup(str(first), "lxml"))
        )

        sleep(1)

        second = Duwo(users[0],
                      session_cache_dir=self.duwo_session_path,
                      call_cache_dir=self.call_cache_dir
                      ).login(
                      ).get_page("https://duwo.multiposs.nl/MachineAvailability.php")

        self.maxDiff=None
        self.assertEqual(first, second)

class TestReservations(unittest.TestCase):
    duwo_session_path = Path("./testsessions")
    call_cache_dir = Path("./call_cache")

    def setUp(self):
        users = get_all_users()
        self.duwo = Duwo(
            users[0],
            session_cache_dir=self.duwo_session_path,
            call_cache_dir=self.call_cache_dir
        )

    def test_reserve(self):
        self.duwo._make_reservation(
            ReservaionTimeSlot(
                pass
            )
        )

