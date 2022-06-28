from urllib3.exceptions import InsecureRequestWarning
from urllib3            import disable_warnings
disable_warnings(InsecureRequestWarning)

from pathlib import Path

import json
import sys
import os

# VERIFY='/home/bloodyfool/devel/mlaundry/cacert.pem'
VERIFY=False

###

import mechanicalsoup
from mechanicalsoup.utils import LinkNotFoundError
import datetime
from dataclasses import dataclass

from enum import Enum

from typing import *

class MachineType(Enum):
    DRYER  = 'Dryer'
    WASHER = 'Washing Mach.'

@dataclass
class Booking:
    start_time: datetime.datetime
    end_time: datetime.datetime
    machine_type: MachineType

@dataclass
class ReservationTimeSlot:
    start_time: datetime.datetime
    end_time: datetime.datetime
    machine_type: MachineType
    available: int
    booked_by_me: bool
    query: str

@dataclass
class User:
    email: str
    passw: str

def get_users(credentials):
    for line in credentials:
        email, passw, sess = line.split()
        yield User(
                email=email,
                passw=passw,
                )

def get_all_users(creds_path="~/.ssh/laundry.creds"):
    with open(os.path.abspath(os.path.expanduser(creds_path)), "r") as credentials_file:
        return list(get_users(credentials_file))

def _parse_datetime(date_str, closest_to: datetime.datetime = None):
    """
    Parses a datetime string without a year to the closest datetime with those values
    input format: "dd-mm 23:40"
    """
    closest_to = closest_to or datetime.datetime.now()

    candidate_dates = [
            f"{closest_to.year-1}-{date_str}",
            f"{closest_to.year  }-{date_str}",
            f"{closest_to.year+1}-{date_str}",
            ]
    datetimes = [datetime.datetime.strptime(date, "%Y-%d-%m %H:%M") for date in candidate_dates]

    return min(datetimes, key=lambda x: abs(x - closest_to))

def _login_browser(user: User, browser):
    # get the login page
    browser.open("https://duwo.multiposs.nl/login/index.php", verify=VERIFY)

    # fill and submit the login form
    try:
        form = browser.select_form('form#FormLogin')
    except LinkNotFoundError:
        # print("Login Blocked")
        print("Blocked until: " + browser.get_current_page().find('span', {'class': 'BtnTxtReload'}).text.split(":", 1)[1])
        exit()
    form['UserInput'] = user.email
    form['PwdInput'] = user.passw
    browser.submit_selected()

    # "activate" the site by going to the link returned after the login
    url = "https://duwo.multiposs.nl" + str(browser.get_current_page().find('script')).split("\'")[1].split("..")[1]
    response = browser.open(url, verify=VERIFY)

    return browser

def write_to_file(filepath: Path, data: str) -> None:
    os.makedirs(filepath.parents[0], exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(data.encode("utf8"))

def read_from_file(filepath: str) -> str:
    try:
        with open(filepath, "rb") as f:
            return f.read().decode("utf8")
    except FileNotFoundError:
        return None

def get_cached(filepath: Path, func: Callable):
    if os.path.isfile(filepath):
        return read_from_file(filepath)
    else:
        data = func()
        write_to_file(filepath, data)
        return data

class Duwo:

    def __init__(self, user: User, session_cache_dir:Path=None, call_cache_dir:Path=None, load_session=True):
        self.session_cache_dir = session_cache_dir or Path("~/.laundry_cache/").expanduser()
        self.call_cache_dir = call_cache_dir and call_cache_dir.expanduser() / user.email

        self.browser = mechanicalsoup.StatefulBrowser()
        self.user = user
        self.user_session_path = self.session_cache_dir / user.email

        if load_session:
            session = self._get_session_cookie_from_disk()
            if session:
                self.load_session(session)

    def _persist_session(self):
        write_to_file(self.user_session_path, self._get_session())

    def _get_session(self):
        return json.dumps(self.browser.session.cookies.get_dict())

    def login(self):
        _login_browser(self.user, self.browser)
        self._persist_session()
        return self

    def _get_session_cookie_from_disk(self):
        return read_from_file(self.user_session_path)

    def load_session(self, session):
        from requests.utils import cookiejar_from_dict
        if session is not None:
            self.browser.session.cookies = cookiejar_from_dict(json.loads(session))

    def _session_active(self, page):
        if "window.location.href = 'index.html';" in str(page):
            return False
        else:
            return True

    def _get_cached_page(self, url):
        if not self.call_cache_dir:
            return None
        from bs4 import BeautifulSoup
        url = url.replace("/", "$")
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        page_str = read_from_file(self.call_cache_dir / url / today)
        if page_str is None:
            return None
        return BeautifulSoup(page_str, "lxml")

    def _set_cached_page(self, url, page):
        if not self.call_cache_dir:
            return
        from shutil import rmtree
        url = url.replace("/", "$")
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        rmtree(self.call_cache_dir / url, ignore_errors=True)
        write_to_file(self.call_cache_dir / url / today, str(page))

    def get_page(self, url, retries=2):
        from bs4 import BeautifulSoup
        cached_page = self._get_cached_page(url)
        if cached_page:
            return cached_page
        if retries <= 0:
            print("Unable to fetch")
            exit()
        self.browser.open(url, verify=VERIFY)
        page = self.browser.get_current_page()
        if not self._session_active(page):
            print(page, file=sys.stderr)
            self.login()
            return self.get_page(url, retries-1)
        self._set_cached_page(url, page)
        return page

    def get_avalability(self):
        page = self.get_page("https://duwo.multiposs.nl/MachineAvailability.php")

        wash_row, dry_row = page.find_all('tr')[1:3]

        any_available_washers = wash_row.find('p', {'class': 'TxtAvailable'})
        if(any_available_washers):
            wash_p = wash_row.find('p')  # wash_p.text = "Available :2"
            wash = wash_p.text.split(":")[1]
        else:
            wash = '0'

        any_available_dryers = dry_row.find('p', {'class': 'TxtAvailable'})
        if(any_available_dryers):
            dry_p = dry_row.find('p')  # dry_p.text = "Available :2"
            dry = dry_p.text.split(":")[1]
        else:
            dry = '0'
        return wash, dry

    def get_machine_type_mapping(self):
        page = self.get_page("https://duwo.multiposs.nl/findmachinetypes.php")
        res = page.find_all('div', {'id': 'BtnMachineType'})
        res = {MachineType(r.find('span').text):r['name'] for r in res}
        return res

    def get_time(self):
        # get the Machine Availability "sub" page
        page = self.get_page("https://duwo.multiposs.nl/MachineAvailability.php")

        # get the second and third row of the only table in the page
        time = page.find('h').text

        format_str = "%m-%d-%y %H:%M:%S"

        return time

    def get_bookings(self):
        page = self.get_page("https://duwo.multiposs.nl/BookingOverview.php")

        rows = page.find_all('tr')[1:]
        for row in rows:
            date, times, _, mtype = [x.text for x in row.find_all('td')[0:4]]
            start, end = times.split("->")

            mtype = MachineType(mtype)
            start = _parse_datetime(f"{date} {start}")
            end = _parse_datetime(f"{date} {end}")
            end = start + self._get_actual_timedelta(end-start, mtype)

            yield Booking(
                    start_time=start,
                    end_time=end,
                    machine_type=mtype,
                    )

    def _get_actual_timedelta(self, duration: datetime.timedelta, mtype: MachineType):
        if mtype == MachineType.WASHER:
            return datetime.timedelta(minutes=45)

        expected_dryer_time = 40
        actual_dryer_time = 35

        minutes = int(duration.seconds / 60 / 40) * 35

        return datetime.timedelta(minutes=minutes)

    def get_reservation_timeslots(self, mtype, date=None) -> List[ReservationTimeSlot]:
        mapping = self.get_machine_type_mapping()
        if not date:
            date = datetime.datetime.now()
        date_str = date.strftime("%d-%m-%Y")
        page = self.get_page(f"https://duwo.multiposs.nl/FindAvailableFromMachineType.php?ObjectMachineTypeID={mapping[mtype]}&Start_Date={date_str}")
        timeslots = page.find_all("div", {"class": ["DivCalendarObjectTijdsBlokNotBooked", "BookedByYou", "BookedNotByYou" ]})
        def map_timeslot(timeslot):
            start, end = timeslot.find("span", {"class": "TijdsBlokTijd"}).text.split(" - ")
            s_h, s_m = start.split(":")
            e_h, e_m = end.split(":")
            if "BookedNotByYou" in timeslot["class"]:
                available    = 0
            elif "BookedByYou" in timeslot["class"]:
                available = -1
            else:
                available = int(timeslot.find("span", {"class": "TijdsBlokVrij"}).text.split(":")[1])
            return ReservationTimeSlot(
                start_time   = date.combine(date, datetime.time(int(s_h), int(s_m))),
                end_time     = date.combine(date, datetime.time(int(e_h), int(e_m))),
                machine_type = mtype,
                available    = available,
                booked_by_me = "BookedByYou" in timeslot["class"],
                query        = timeslot.get("name", "0000000")
            )
        return [map_timeslot(timeslot) for timeslot in timeslots]

    def _make_reservation(self, reservation: ReservationTimeSlot):#, reservation: ReservationTimeSlot, count: int, allSlots: List[ReservationTimeSlot]):
        mapping = self.get_machine_type_mapping()
        self.get_page(f"https://duwo.multiposs.nl/FindAvailableFromMachineType.php?ObjectMachineTypeID={mapping[reservation.machine_type]}")
        self.get_page(f"https://duwo.multiposs.nl/AnnouncmentBooking.php?value={reservation.query}")
        self.get_page(f"https://duwo.multiposs.nl/ConfirmCreateBooking.php?value={reservation.query}")
        self.get_page(f"https://duwo.multiposs.nl/CreateBooking.php?value={reservation.query}")

    def _remove_reservation(self, reservation: ReservationTimeSlot ):#, count: int, allSlots: List[ReservationTimeSlot]):
        page = self.get_page(f"https://duwo.multiposs.nl/AnnouncmentBooking.php?ResNr={reservation.query}")
        page = self.get_page(f"https://duwo.multiposs.nl/DeleteBooking.php")

def open_browser_with_chromium_session(user):
    # from browser import set_cookie_in_brave
    session = get_cookie_from_brave("duwo.multiposs.nl", "PHPSESSID")
    duwo = Duwo(user, load_session=False)
    duwo.load_session(json.dumps({"PHPSESSID":session}))
    duwo.login()

    # Sad... Cookie gets set, but a new one is still requested

    # cookie_obj = requests.cookies.create_cookie(name='PHPSESSID', value='VF8mr%2CxGqkZdBWWCb1Gqw5YCog8', domain='duwo.multiposs.nl')
    # browser.session.cookies.set_cookie(cookie_obj)  # This will add your new cookie to existing cookies

    # return

    # import time
    # time.sleep(10)

    os.system('brave https://duwo.multiposs.nl/main.php &')

def show_users():
    users = get_all_users()
    for index, user in enumerate(users):
        print(f" {index} | {user.email}")

def show_open_reservations(user_index, days_ahead=0, machine_type=MachineType.WASHER):
    user = get_all_users()[user_index]
    duwo = Duwo(user, load_session=False)
    duwo.login()
    day = datetime.datetime.today() + datetime.timedelta(days=int(days_ahead))
    reservations = duwo.get_reservation_timeslots(machine_type, day)
    for reservation in reservations:
        print(f" {reservation.start_time.strftime('%y-%m-%d %H:%M')} | {reservation.available}")

def make_reservation(user_index, days_ahead=0, start_hour=0, machine_type=MachineType.WASHER):
    user = get_all_users()[user_index]
    duwo = Duwo(user, load_session=False)
    duwo.login()
    day = datetime.datetime.today() + datetime.timedelta(days=int(days_ahead))
    reservations = duwo.get_reservation_timeslots(machine_type, day)
    reservation = [t for t in reservations if t.start_time.time() >= datetime.time(int(start_hour), 0) and t.available > 0][0] # first available machine after 'start_hour'
    duwo._make_reservation(reservation)
    reservations = duwo.get_reservation_timeslots(machine_type, day)
    for reservation in reservations:
        print(f" {reservation.start_time.strftime('%y-%m-%d %H:%M')} | {reservation.available}")

def remove_reservations(user_index, days_ahead=0, machine_type=MachineType.WASHER):
    user = get_all_users()[user_index]
    duwo = Duwo(user, load_session=False)
    duwo.login()
    day = datetime.datetime.today() + datetime.timedelta(days=int(days_ahead))
    reservations = duwo.get_reservation_timeslots(machine_type, day)
    reservations = [t for t in reservations if t.booked_by_me]
    for reservation in reservations:
        duwo._remove_reservation(reservation)
    reservations = duwo.get_reservation_timeslots(machine_type, day)
    for reservation in reservations:
        print(f" {reservation.start_time.strftime('%y-%m-%d %H:%M')} | {reservation.available}")
