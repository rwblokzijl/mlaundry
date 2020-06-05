#!/usr/bin/env pipenv-shebang
#!/usr/bin/python3

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

from util import *

import os

# disable warnings about the https verify=False, which is needed because of
# shitty certs? idfk, just dont reuse an important password for the site
disable_warnings(InsecureRequestWarning)

# get login info from file
CREDS_PATH = "~/.ssh/laundry.creds"
with open(os.path.abspath(os.path.expanduser(CREDS_PATH)), "r") as credentials_file:
    users = { line.split()[0] : line.split()[1] for line in credentials_file }
    # user_email = credentials_file.readline().strip()
    # password = credentials_file.readline().strip()

username = next(iter(users))
passw = users[username]

def print_laun(users):
    bookings = get_all_bookings(users)
    # print([start.time() for start, _, _ in bookings])
    next_book = get_next_finished_booking_if_running(bookings, delta=timedelta(minutes=10))
    if next_book:
        start, end, mtype = next_book
        if now < end: # Not done yet
            print(f'{machine_map[mtype]} is done at: {end.strftime("%H:%M")}')
            print(f'{machine_map[mtype]} done: {end.strftime("%H:%M")}')
            if now + timedelta(minutes=10) > end: # Done within 10 minutes
                # Make notify but only once when its done
                epoch = f"laundry-{start.strftime('%s')}"
                os.system(f"""[ -f /tmp/{epoch} ] || (((echo "notify-send 'Laundry: ' '{machine_map[mtype]} Done!'" | at {end.strftime("%H:%M")}) &>/dev/null);touch /tmp/{epoch}) """)
                print("#B8BB26")
        else: #Done
            print(f'{machine_map[mtype]} finished!')
            print(f'{machine_map[mtype]} finished!')
            print("#FABD2F")
        return
    start_book = get_next_starting_booking(bookings, delta=timedelta(minutes=10))
    if start_book:
        start, end, mtype = start_book
        if start < now:
            print(f'{machine_map[mtype]} is booked for: {start.strftime("%H:%M")}')
            print(f'{machine_map[mtype]} booked: {start.strftime("%H:%M")}')
        else: # running now
            print(f'{machine_map[mtype]} is booked for: NOW!')
            print(f'{machine_map[mtype]} booked NOW!')
            print("#FABD2F")
        return
    print_wash_dry(username, passw)

# print_wash_dry(username, passw)
try:
    print_laun(users)
except:
    print("Error")
