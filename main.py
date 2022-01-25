#!/usr/bin/env pipenv-shebang

from laundry.laundry import print_laun, get_users
from laundry.duwo import Duwo

import os
import argparse

def get_all_users():
    with open(os.path.abspath(os.path.expanduser("~/.ssh/laundry.creds")), "r") as credentials_file:
        return list(get_users(credentials_file))

def get_all_bookings(users):
    for user in users:
        yield from Duwo(user)._get_bookings()

def print_laundry():
    users = get_all_users()
    bookings = list(get_all_bookings(users))
    wash, dry = Duwo(users[0]).get_avalability()
    print_laun(users, bookings, wash, dry)

def reservations():
    users = get_all_users()
    Duwo(users[0]).get_reservations()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reservations', '-r', action='store_true')
    args = parser.parse_args()
    if args.reservations:
        return reservations()
    else:
        return print_laundry()

if __name__ == '__main__':
    print_laundry()
