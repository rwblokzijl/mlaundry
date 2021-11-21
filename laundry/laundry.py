#!/usr/bin/env pipenv-shebang

import os
from datetime import timedelta
from typing import *

from laundry.duwo import User, Booking, now

ICON = ""

def get_users(credentials):
    for line in credentials:
        email, passw, sess = line.split()
        yield User(
                email=email,
                passw=passw,
                session_key=sess
                )

def print_wash_dry(user: User, wash, dry):
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

def print_laun(users, bookings, wash, dry):
    next_book = get_next_finished_booking_if_running(bookings, delta=timedelta(minutes=10))
    if next_book is not None:
        mtype = next_book
        if now < next_book.end_time: # Not done yet
            print(f'{ICON} done: {next_book.end_time.strftime("%H:%M")} {wash};{dry}')
            print(f'{ICON} done: {next_book.end_time.strftime("%H:%M")} {wash};{dry}')
            if now + timedelta(minutes=10) > next_book.end_time: # Done within 10 minutes
                # Make notify but only once when its done
                epoch = f"laundry-{next_book.start_time.strftime('%s')}"
                os.system(f"""[ -f /tmp/{epoch} ] || (((echo "notify-send 'Laundry: ' '{next_book.machine_type.value} Done!'" | at {next_book.end_time.strftime("%H:%M")}) &>/dev/null);touch /tmp/{epoch}) """)
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
    print_wash_dry(users[0], wash, dry)

