"""
Python version 3.7.0
Script version 1.0

Avaialble clients:
	* Plum Products Australia Ltd(461162D2-90C7-BF4E-A905-000000000004)

"""
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `vx_freight_provider` \
                FROM `dme_bookings` \
                WHERE `b_dateBookedDate` is NULL and `b_status`=%s and `kf_client_id`=%s and \
                (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                ORDER BY id DESC \
                LIMIT 10"
        cursor.execute(
            sql, ("Ready for booking", "461162D2-90C7-BF4E-A905-000000000004", "")
        )
        bookings = cursor.fetchall()

        return bookings


def do_book(booking):
    url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/book/"
    data = {"booking_id": "id"}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - ", s0)
    return data0


def do_get_label(booking):
    url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/get-label/"
    data = {"booking_id": "id"}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)
    return data0


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to process: ", len(bookings))

    if len(bookings) > 0:
        for booking in bookings:
            print("#200 - Processing: ***", booking["b_bookingID_Visual"], "***")
            result = do_book(booking)

            if (
                {booking["vx_freight_provider"].lower()} not in ["hunter", "capital"]
                and "message" in result
                and "Successfully booked" in result["message"]
            ):
                do_get_label(booking)


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
        print("#904 Error: ", str(e))
        set_option(mysqlcon, "auto_book_label", False, time1)

    mysqlcon.close()
    print("#999 Finished %s" % datetime.datetime.now())
