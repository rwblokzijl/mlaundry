#!/usr/bin/env pipenv-shebang

from laundry.laundry import print_laun, get_users
from laundry.duwo import Duwo, open_browser_with_chromium_session, make_reservation, remove_reservations, show_open_reservations

import os
import sys
import argparse

def get_all_users(creds_path="~/.ssh/laundry.creds"):
    with open(os.path.abspath(os.path.expanduser(creds_path)), "r") as credentials_file:
        return list(get_users(credentials_file))

def get_all_bookings(users):
    for user in users:
        yield from Duwo(user).get_bookings()

def print_laundry():
    users = get_all_users()
    bookings = list(get_all_bookings(users))
    wash, dry = Duwo(users[0]).get_avalability()
    print_laun(users, bookings, wash, dry)

def main():
    parser = argparse.ArgumentParser()
    return print_laundry()
    # parser.add_argument('--reservations', '-r', action='store_true')
    # args = parser.parse_args()
    # if args.reservations:
    #     return reservations()
    # else:
    #     return print_laundry()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print_laundry()
    elif sys.argv[1] == "browse":
        users = get_all_users()
        open_browser_with_chromium_session(users[0])
    elif sys.argv[1] == "show":
        users = get_all_users()
        show_open_reservations(users[0], *sys.argv[2:])
    elif sys.argv[1] == "res":
        users = get_all_users()
        make_reservation(users[0], *sys.argv[2:])
    elif sys.argv[1] == "rem":
        users = get_all_users()
        remove_reservations(users[0])

