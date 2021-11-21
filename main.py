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

def main():
    users = get_all_users()
    bookings = list(get_all_bookings(users))
    wash, dry = Duwo(users[0]).get_avalability()
    print_laun(users, bookings, wash, dry)

if __name__ == '__main__':
    main()
