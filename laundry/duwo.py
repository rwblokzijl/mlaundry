from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
# VERIFY='/home/bloodyfool/devel/mlaundry/cacert.pem'
VERIFY=False

###

import mechanicalsoup
from mechanicalsoup.utils import LinkNotFoundError
from datetime import datetime, timedelta
from dataclasses import dataclass

from enum import Enum

from typing import *

now = datetime.now()
# now = datetime(2021, 8, 11, 17, 30) # before
# now = datetime(2021, 8, 11, 17, 50) # during wash
# now = datetime(2021, 8, 11, 18, 20) # between
# now = datetime(2021, 8, 11, 18, 50) # during dry
# now = datetime(2021, 8, 11, 19, 50) # after

class MachineType(Enum):
    DRYER  = 'Dryer'
    WASHER = 'Washing Mach.'

@dataclass
class Booking:
    start_time: datetime
    end_time: datetime
    machine_type: MachineType

@dataclass
class User:
    email: str
    passw: str
    session_key: str

def _parse_datetime(date_str, closest_to: datetime = now):
    """
    Parses a datetime string without a year to the closest datetime with those values
    input format: "dd-mm 23:40"
    """

    candidate_dates = [
            f"{closest_to.year-1}-{date_str}",
            f"{closest_to.year  }-{date_str}",
            f"{closest_to.year+1}-{date_str}",
            ]
    datetimes = [datetime.strptime(date, "%Y-%d-%m %H:%M") for date in candidate_dates]

    return min(datetimes, key=lambda x: abs(x - closest_to))

def _get_logged_browser(user: User, browser=None):
    if not browser:
        browser = mechanicalsoup.StatefulBrowser()

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

class Duwo:

    def __init__(self, user: User):
        self.browser = _get_logged_browser(user)

    def get_page(self, url):
        self.browser.open(url, verify=VERIFY)
        return self.browser.get_current_page()

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

    def get_reservations(self, type=MachineType.WASHER) -> List[Booking]:
        mapping = self.get_machine_type_mapping()
        date = "22-11-2021"
        type = "45"
        page = self.get_page(f"https://duwo.multiposs.nl/FindAvailableFromMachineType.php?ObjectMachineTypeID={type}&Start_Date={date}")
        cal = page.find("div", {"id": "CalendarObject"})
        print(cal)

    def get_time(self):
        # get the Machine Availability "sub" page
        page = self.get_page("https://duwo.multiposs.nl/MachineAvailability.php")

        # get the second and third row of the only table in the page
        time = page.find('h').text

        format_str = "%m-%d-%y %H:%M:%S"

        return time

    def _get_bookings(self):
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

    def _get_actual_timedelta(self, time, mtype):
        expected_time = {
                MachineType.DRYER: 40,
                MachineType.WASHER: 35
                }
        actual_time = {
                MachineType.DRYER: 35,
                MachineType.WASHER: 45
                }

        expected_minutes = time.seconds / 60
        if expected_time[mtype] < expected_minutes < 59:
            return timedelta(minutes=actual_time[mtype])

        actual_minutes  = (expected_minutes / expected_time[mtype]) * actual_time[mtype]
        return timedelta(minutes=actual_minutes)


# def open_browser_with_chromium_session(user, session_key=None):
#     browser = mechanicalsoup.StatefulBrowser()

#     cookie_obj = requests.cookies.create_cookie(name='PHPSESSID', value='VF8mr%2CxGqkZdBWWCb1Gqw5YCog8', domain='duwo.multiposs.nl')
#     browser.session.cookies.set_cookie(cookie_obj)  # This will add your new cookie to existing cookies

#     Duwo(user)._get_logged_browser(user, browser=browser)

#     os.system("brave https://duwo.multiposs.nl/main.php &")

