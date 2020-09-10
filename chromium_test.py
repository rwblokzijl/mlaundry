#!/usr/bin/env pipenv-shebang

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

from util import *
import os
import mechanicalsoup

# disable warnings about the https verify=False, which is needed because of
# shitty certs? idfk, just dont reuse an important password for the site
disable_warnings(InsecureRequestWarning)


CREDS_PATH = "~/.ssh/laundry.creds"
with open(os.path.abspath(os.path.expanduser(CREDS_PATH)), "r") as credentials_file:
    users = { line.split()[0] : line.split()[1] for line in credentials_file }
    # user_email = credentials_file.readline().strip()
    # password = credentials_file.readline().strip()

username = next(iter(users))
passw = users[username]

open_browser_with_chromium_session(username, passw)


