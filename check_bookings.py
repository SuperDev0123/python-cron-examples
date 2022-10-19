"""
Python version 3.7.0
Script version 1.0

Avaialble clients:
    * Plum Products Australia Ltd(461162D2-90C7-BF4E-A905-000000000004)
    * Jason L
    * Bathroom Sales Direct

"""
import traceback
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    API_URL,
    USERNAME,
    PASSWORD,
)
from _options_lib import get_option, set_option
from _email_lib import send_email

TYPE_1 = 1  # Plum
TYPE_2 = 2  # JasonL & BSD(Bathroom Sales Direct)


def get_token():
    url = API_URL + "/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        # print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def get_duplicate_booking_visual_ids(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, b_bookingID_Visual, v_FPBookingNumber, b_client_name \
                FROM dme_bookings \
                GROUP BY b_bookingID_Visual \
                HAVING COUNT(b_bookingID_Visual) > 1;"
        cursor.execute(
            sql,
        )
        bookings = cursor.fetchall()
        return bookings

def get_duplicate_pk_booking_ids(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, pk_booking_id, v_FPBookingNumber, b_client_name \
                FROM dme_bookings \
                GROUP BY pk_booking_id \
                HAVING COUNT(pk_booking_id) > 1;"
        cursor.execute(
            sql,
        )
        bookings = cursor.fetchall()
        return bookings


def send_email_to_admins(bookings, type):
    text = (
        f"This email is from DME CRONJOB:"
        + f"\n\n\n\n{type.upper()} Info:\n{json.dumps(bookings, indent=4)}"
        + f"\n\n\n\nPlease reply to all if you are going to resolve the issue.\nAfter resolved, reply to all - 'Resolved'"
        + f"\nWhen you got unknown issue while resolving issue, please contact DME lead developer - Gold(goldj@deliver-me.com.au)"
        + f"\n\nRegards,\nDME CRONJOB"
    )
    send_email(
        ["pete2@deliver-me.com.au", "goldj@deliver-me.com.au", "daniely@deliver-me.com.au"],
        ["dev.deliverme@gmail.com"],
        [],
        f"Error happened while '{type.upper()}'",
        text,
    )

def do_process(mysqlcon):
    token = get_token()

    bookings = get_duplicate_booking_visual_ids(mysqlcon)  # JasonL
    print("#202 - Duplicate Booking Visual IDs: ", len(bookings))

    if len(bookings) > 0:
        send_email_to_admins(bookings, "Duplicated Booking Visual ID")
        
    bookings = get_duplicate_pk_booking_ids(mysqlcon)  # JasonL
    print("#202 - Duplicate PK Booking IDs: ", len(bookings))

    if len(bookings) > 0:
        send_email_to_admins(bookings, "Duplicated PK Booking ID")

if __name__ == "__main__":
    print("#900 Started %s" % datetime.datetime.now())
    time1 = time.time()

    try:
        mysqlcon = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        print("Mysql DB connection error!", e)
        exit(1)

    try:
        option = get_option(mysqlcon, "auto_book_label")

        if int(option["option_value"]) == 0:
            print("#905 - `auto_book_label` option is OFF")
        elif option["is_running"]:
            print("#905 - `auto_book_label` script is already RUNNING")
        else:
            print("#906 - `auto_book_label` option is ON")
            time1 = time.time()
            set_option(mysqlcon, "auto_book_label", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            print("#919 - Finished processing!")
            set_option(mysqlcon, "auto_book_label", False, time1)
    except Exception as e:
        traceback.print_exc()
        print("#904 Error: ", str(e))
        set_option(mysqlcon, "auto_book_label", False, time1)

    mysqlcon.close()
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())
