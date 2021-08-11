#!/usr/bin/env pipenv-shebang

from laundry.laundry import print_laun, get_users

import os

def main():
    with open(os.path.abspath(os.path.expanduser("~/.ssh/laundry.creds")), "r") as credentials_file:
        users = list(get_users(credentials_file))

    print_laun(users)

if __name__ == '__main__':
    main()
