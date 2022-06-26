#!/usr/bin/env pipenv-shebang

from laundry.laundry import print_laun

from laundry.duwo import Duwo
from laundry.duwo import MachineType
from laundry.duwo import get_all_users
from laundry.duwo import open_browser_with_chromium_session

from laundry.duwo import make_reservation
from laundry.duwo import remove_reservations
from laundry.duwo import show_open_reservations
from laundry.duwo import show_users

import os
import sys
import argparse

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
    # parser.add_argument('--reservations', '-r', action='store_true')
    # args = parser.parse_args()
    # if args.reservations:
    #     return reservations()
    # else:
    #     return print_laundry()
    # return print_laundry()

def parse_machine_type(string):
    if string.lower() in ["d", "dry", "dryer"]:
        return MachineType.DRYER
    elif string.lower() in ["w", "wash", "washing-machine"]:
        return MachineType.WASHER
    else:
        return string

def make_parser():
    parser = argparse.ArgumentParser()

    main_subparsers = parser.add_subparsers()

    users  = main_subparsers.add_parser("users",  help="Shows all users and their indexes")
    show   = main_subparsers.add_parser("show",   help="Shows reservation statuses")
    book   = main_subparsers.add_parser("book",   help="Books a reservation")
    cancel = main_subparsers.add_parser("cancel", help="Cancels a reservation")
    for sub in [show, book, cancel]:
        sub.add_argument('--user-index',   '-u', type=int,                default=0, help="Index of the user")
        sub.add_argument('--days-ahead',   '-d', type=int,                default=0, help="Days from today")
        sub.add_argument('--machine-type', '-m', type=parse_machine_type, default=MachineType.WASHER, choices=[MachineType.WASHER, MachineType.DRYER], help="Machine type")
    book.add_argument('--start-hour', '-s', type=int, default=0, help="Hour from which to book first available slot")

    parser.set_defaults(func=print_laundry)
    show.set_defaults(func=show_open_reservations)
    book.set_defaults(func=make_reservation)
    cancel.set_defaults(func=remove_reservations)
    users.set_defaults(func=show_users)
    return parser

if __name__ == '__main__':
    args = make_parser().parse_args(sys.argv[1:])
    func = args.func
    args = vars(args)
    args.pop("func")
    func(**args)

# laundry
#   reservations (r)
#      show (s)
#      book (b)
#      cancel (c)




