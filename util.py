import mechanicalsoup
import requests
import os

from datetime import datetime, timedelta

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

now = datetime.now()
# datetime(2020, 7, 1, 9, 50)
# now = datetime.now() - timedelta(minutes=15)
# now = datetime.now() - timedelta(days=1)
# now = datetime.now() - timedelta(hours=3)
# now = datetime.now() - timedelta(hours=2, minutes=0)

# print(f'time: {now.strftime("%H:%M")}')

# get login info from file
def get_users(CREDS_PATH = "~/.ssh/laundry.creds"):
    with open(os.path.abspath(os.path.expanduser(CREDS_PATH)), "r") as credentials_file:
        users = dict()
        sessions = dict()
        for line in credentials_file:
            user = line.split()
            if len(user) == 2:
                user.append(None)
            users[user[0]] = user[1]
            sessions[user[0]] = user[2]
        return users

# browser stuff
def open_browser_with_chromium_session(username, password, session_key=None):
    browser = mechanicalsoup.StatefulBrowser()

    cookie_obj = requests.cookies.create_cookie(name='PHPSESSID', value='VF8mr%2CxGqkZdBWWCb1Gqw5YCog8', domain='duwo.multiposs.nl')
    browser.session.cookies.set_cookie(cookie_obj)  # This will add your new cookie to existing cookies

    get_logged_browser(username, password, browser=browser)

    os.system("chromium https://duwo.multiposs.nl/main.php &")


def get_logged_browser(user_email, password, browser=None):
    # proxies = {
    #         'https': 'socks5://wesselb94@gmail.com:blokzijlfamVPN@socks-nl2.nordvpn.com:1080'
    #         }
    if not browser:
        browser = mechanicalsoup.StatefulBrowser()
        # browser.session.proxies = proxies

    # get the login page
    response = browser.open("https://duwo.multiposs.nl/login/index.php", verify=False)

    # fill and submit the login form
    try:
        form = browser.select_form('form#FormLogin')
    except:
        # print("Login Blocked")
        print("Blocked until: " + browser.get_current_page().find('span', {'class': 'BtnTxtReload'}).text.split(":", 1)[1])
        exit()
    form['UserInput'] = user_email
    form['PwdInput'] = password
    browser.submit_selected()

    # print(browser.get_current_page())

    # tmp = browser.get_current_page().find('script')
    # print(str(tmp))
    # "activate" the site by going to the link returned after the login
    url = "https://duwo.multiposs.nl" + str(browser.get_current_page().find('script')).split("\'")[1].split("..")[1]
    response = browser.open(url, verify=False)

    return browser

def get_avalability(user, password):
    browser = get_logged_browser(user, password)

    # get the Machine Availability "sub" page
    response = browser.open("https://duwo.multiposs.nl/MachineAvailability.php", verify=False)

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
    if expected_time_map[mtype] < expected_minutes < 59:
        return timedelta(minutes=actual_time_map[mtype])
    actual_minutes  = (expected_minutes / expected_time_map[mtype]) * actual_time_map[mtype]
    return timedelta(minutes=actual_minutes)

def get_bookings(u, p):
    browser = get_logged_browser(u, p)
    browser.open("https://duwo.multiposs.nl/BookingOverview.php", verify=False)

    # parse it for data
    page = browser.get_current_page()

    rows = page.find_all('tr')[1:]
    ans = list()
    for row in rows:
        date, times, _, mtype = [x.text for x in row.find_all('td')[0:4]]
        start, end = times.split("->")

        mtype = rev_machine_map[mtype]
        start = get_datetime(f"{date} {start}")
        end = get_datetime(f"{date} {end}")
        end = start + get_actual_timedelta(end-start, mtype)

        ans.append((start, end, mtype))
    return ans

def print_wash_dry(user, password):
    wash, dry = get_avalability(user, password)

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

def get_next_finished_booking_if_running(bookings, delta):
    best_dist = None
    best = None
    for booking in bookings:
        start, end, mtype = booking

        if start < now and now - delta < end: #delta for extra time to show its done
            dist = abs(end - now)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = booking
    return best

def get_next_starting_booking(bookings, delta):
    best_dist = None
    best = None
    for booking in bookings:
        start, end, mtype = booking

        if now - delta < start:
            dist = abs(end - now)
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
    ans = []
    for user_email, password in users.items():
        ans += get_bookings(user_email, password)
    return ans


def get_time(user, password):
    browser = get_logged_browser(user, password)

    # get the Machine Availability "sub" page
    response = browser.open("https://duwo.multiposs.nl/MachineAvailability.php", verify=False)

    # parse it for data
    page = browser.get_current_page()

    # get the second and third row of the only table in the page
    time = page.find('h').text

    format_str = "%m-%d-%y %H:%M:%S"

    return time

