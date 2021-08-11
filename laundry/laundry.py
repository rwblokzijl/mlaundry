#!/usr/bin/env pipenv-shebang

import mechanicalsoup
import requests
import os

from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import *

# disable warnings about the https verify=False, which is needed because of
# shitty certs? idfk, just dont reuse an important password for the site
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)
# VERIFY='/home/bloodyfool/devel/mlaundry/cacert.pem'
VERIFY=False

EXPECTED_WASHER_TIME = 35
EXPECTED_DRYER_TIME  = 40

ACTUAL_WASHER_TIME = 45
ACTUAL_DRYER_TIME  = 35

ICON = ""

expected_time_map = {
        'd': EXPECTED_DRYER_TIME,
        'w': EXPECTED_WASHER_TIME
        }

actual_time_map = {
        'd': ACTUAL_DRYER_TIME,
        'w': ACTUAL_WASHER_TIME
        }

machine_map = {
        'd': 'Dryer',
        'w': 'Washer'
        }

rev_machine_map = {
        'Dryer'         : 'd',
        'Washing Mach.' : 'w'
        }

class MachineType(Enum):
    DRYER  = 'Dryer'
    WASHER = 'Washing Mach.'

now = datetime.now()
# now = datetime(2021, 8, 11, 18, 50)
# now = datetime.now() - timedelta(minutes=15)
# now = datetime.now() - timedelta(days=1)
# now = datetime.now() - timedelta(hours=3)
# now = datetime.now() - timedelta(hours=2, minutes=0)

# print(f'time: {now.strftime("%H:%M")}')

@dataclass
class Booking:
    start_time: datetime
    end_time: datetime
    machine_type: MachineType
    _now: datetime = now

@dataclass
class User:
    email: str
    passw: str
    session_key: str

def get_users(credentials):
    for line in credentials:
        email, passw, sess = line.split()
        yield User(
                email=email,
                passw=passw,
                session_key=sess
                )

def get_logged_browser(user: User, browser=None):
    """"""
    # proxies = {
    #         'https': 'socks5://wesselb94@gmail.com:blokzijlfamVPN@socks-nl2.nordvpn.com:1080'
    #         }
    if not browser:
        browser = mechanicalsoup.StatefulBrowser()
        # browser.session.proxies = proxies

    # get the login page
    response = browser.open("https://duwo.multiposs.nl/login/index.php", verify=VERIFY)

    # fill and submit the login form
    try:
        form = browser.select_form('form#FormLogin')
    except:
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

def get_avalability(user: User):
    browser = get_logged_browser(user)

    # get the Machine Availability "sub" page
    browser.open("https://duwo.multiposs.nl/MachineAvailability.php", verify=VERIFY)

    # parse it for data
    page = browser.get_current_page()

    # get the second and third row of the only table in the page
    wash_row, dry_row = page.find_all('tr')[1:3]

    # if there are no machines available the row has a <p> with class="TxtNotAvailable" else it has class="TxtAvailable"
    if(wash_row.find('p', {'class': 'TxtAvailable'})):
        wash_p = wash_row.find('p')  # wash_p.text = "Available :2"
        wash = wash_p.text.split(":")[1]
    else:
        wash = '0'

    # the same for dryers
    if(dry_row.find('p', {'class': 'TxtAvailable'})):
        dry_p = dry_row.find('p')  # dry_p.text = "Available :2"
        dry = dry_p.text.split(":")[1]
    else:
        dry = '0'
    return wash, dry

def get_actual_timedelta(time, mtype):
    expected_minutes = time.seconds / 60
    actual_minutes  = (expected_minutes / expected_time_map[mtype]) * actual_time_map[mtype]
    return timedelta(minutes=actual_minutes)

def parse_bookings(user: User):
    browser = get_logged_browser(user)
    browser.open("https://duwo.multiposs.nl/BookingOverview.php", verify=VERIFY)

    # parse it for data
    page = browser.get_current_page()

    rows = page.find_all('tr')[1:]
    for row in rows:
        date, times, _, omtype = [x.text for x in row.find_all('td')[0:4]]
        start, end = times.split("->")

        mtype = rev_machine_map[omtype]
        start = get_datetime(f"{date} {start}")
        end = get_datetime(f"{date} {end}")
        end = start + get_actual_timedelta(end-start, mtype)

        b = Booking(
                start_time=start,
                end_time=end,
                machine_type=MachineType(omtype)
                )
        yield b

def print_wash_dry(user: User):
    wash, dry = get_avalability(user)

    # print("wash/dry: (" + wash + "/" + dry + ")")
    print(f"{ICON} {wash};{dry}")
    print(f"{ICON} {wash};{dry}")
    if(int(wash) == 0):
        pass
    elif(int(wash) == 1):
        pass
    elif(int(wash) == 2):
        print("#FABD2F")
    elif(int(wash) == 3):
        print("#B8BB26")
    elif(int(wash) == 4):
        print("#B8BB26")

# helpers

def get_next_finished_booking_if_running(bookings: List[Booking], delta) -> Optional[Booking]:
    best_dist = None
    best = None
    for booking in bookings:
        if booking.start_time < now and now - delta < booking.end_time: #delta for extra time to show its done
            dist = abs(booking.end_time - now)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = booking
    return best

def get_next_starting_booking(bookings: List[Booking], delta) -> Optional[Booking]:
    best_dist = None
    best = None
    for booking in bookings:
        if now - delta < booking.start_time:
            dist = abs(booking.end_time - now)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = booking
    return best

def get_datetime(date_str):
    # date_str = "05-06 23:40"
    format_str = "%Y-%d-%m %H:%M"

    years = [f"{now.year}-{date_str}", f"{now.year+1}-{date_str}",
            f"{now.year-1}-{date_str}"]

    best_dist = None
    best = None

    for year in years:
        datetime_obj = datetime.strptime(year, format_str)
        dist = abs(datetime_obj - now)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best = datetime_obj

    return best

def get_all_bookings(users):
    for user in users:
        yield from parse_bookings(user)

def get_time(user: User):
    browser = get_logged_browser(user)

    # get the Machine Availability "sub" page
    response = browser.open("https://duwo.multiposs.nl/MachineAvailability.php", verify=VERIFY)

    # parse it for data
    page = browser.get_current_page()

    # get the second and third row of the only table in the page
    time = page.find('h').text

    format_str = "%m-%d-%y %H:%M:%S"

    return time

def print_laun(users):
    bookings = list(get_all_bookings(users))
    next_book = get_next_finished_booking_if_running(bookings, delta=timedelta(minutes=10))
    wash, dry = get_avalability(users[0])
    if next_book is not None:
        mtype = next_book
        if now < next_book.end_time: # Not done yet
            print(f'{ICON} done: {next_book.end_time.strftime("%H:%M")} {wash};{dry}')
            print(f'{ICON} done: {next_book.end_time.strftime("%H:%M")} {wash};{dry}')
            if now + timedelta(minutes=10) > next_book.end_time: # Done within 10 minutes
                # Make notify but only once when its done
                epoch = f"laundry-{next_book.start_time.strftime('%s')}"
                os.system(f"""[ -f /tmp/{epoch} ] || (((echo "notify-send 'Laundry: ' '{next_book.machine_type.value} Done!'" | at {end.strftime("%H:%M")}) &>/dev/null);touch /tmp/{epoch}) """)
                print("#B8BB26")
        else: #Done
            print(f'{ICON} {next_book.machine_type.value} finished! {wash};{dry}')
            print(f'{ICON} {next_book.machine_type.value} finished! {wash};{dry}')
            print("#FABD2F")
        return
    start_book = get_next_starting_booking(bookings, delta=timedelta(minutes=10))
    if start_book:
        if start_book.start_time > now:
            print(f'{ICON} booked {start_book.start_time.strftime("%H:%M")} {wash};{dry}')
            print(f'{ICON} {start_book.start_time.strftime("%H:%M")} {wash};{dry}')
        else: # running now
            print(f'{ICON} NOW! {wash};{dry}')
            print(f'{ICON} NOW! {wash};{dry}')
            print("#FABD2F")
        return
    print_wash_dry(users[0])

# browser stuff
def open_browser_with_chromium_session(user, session_key=None):
    browser = mechanicalsoup.StatefulBrowser()

    cookie_obj = requests.cookies.create_cookie(name='PHPSESSID', value='VF8mr%2CxGqkZdBWWCb1Gqw5YCog8', domain='duwo.multiposs.nl')
    browser.session.cookies.set_cookie(cookie_obj)  # This will add your new cookie to existing cookies

    get_logged_browser(user, browser=browser)

    os.system("brave https://duwo.multiposs.nl/main.php &")

