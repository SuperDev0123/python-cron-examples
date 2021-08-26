# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `vx_freight_provider`=%s and `b_dateBookedDate` is NULL and `b_status`=%s and \
                (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                ORDER BY id DESC \
                LIMIT 10"
        cursor.execute(sql, ("Sendle", "Booked", ""))
        bookings = cursor.fetchall()

        return bookings


def do_book(booking):
    url = API_URL + "/fp-api/sendle/book/"
    data = {}
    data["booking_id"] = booking["id"]

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - ", s0)
    return data0


def do_create_and_get_label(booking):
    url = API_URL + "/fp-api/sendle/get-label/"
    data = {}
    data["booking_id"] = booking["id"]

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)


def do_process(mysqlcon):
    # Get 3 ST bookings
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to process: ", len(bookings))

    if len(bookings) > 0:
        time.sleep(5)

        for booking in bookings:
            print("#200 - Processing: ***", booking["b_bookingID_Visual"], "***")
            # result = do_book(booking)

            # if "message" in result and "Successfully booked" in result["message"]:
            do_create_and_get_label(booking)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())

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
    except:
        print("Mysql DB connection error!")
        exit(1)

    try:
        do_process(mysqlcon)
    except OSError as e:
        print(str(e))

    mysqlcon.close()
    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
