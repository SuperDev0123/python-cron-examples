# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def get_token():
    # BioPak credential
    USERNAME = "biopak"
    PASSWORD = "biopak#123"

    url = API_URL + "/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def get_bookings(mysqlcon, type="not-booked"):
    with mysqlcon.cursor() as cursor:
        if type == "not-booked":
            sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture`, `b_client_warehouse_code` \
                    FROM `dme_bookings` \
                    WHERE `vx_freight_provider`=%s and `b_dateBookedDate` is NULL and `b_status`=%s and \
                    (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                    ORDER BY id DESC \
                    LIMIT 10"
            cursor.execute(sql, ("StarTrack", "Ready for Booking", ""))
        elif type == "missing-label":
            sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture`, `b_client_warehouse_code` \
                    FROM `dme_bookings` \
                    WHERE `vx_freight_provider`=%s and `b_dateBookedDate` is not NULL and `b_status`=%s and \
                    `z_label_url` is NULL and z_CreatedTimestamp > '2020-01-01' and \
                    (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                    ORDER BY id DESC \
                    LIMIT 10"
            cursor.execute(sql, ("StarTrack", "Booked", ""))
        bookings = cursor.fetchall()

        return bookings


def do_book(booking, token):
    url = API_URL + "/fp-api/startrack/book/"
    data = {}
    data["booking_id"] = booking["id"]
    headers = {"Authorization": f"JWT {token}"}
    response = requests.post(url, json=data, headers=headers)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - ", s0)
    return data0


def do_create_and_get_label(booking, token):
    if booking["b_client_warehouse_code"] in ["BIO - RIC", "BIO - HAZ"]:
        url = API_URL + "/build-label/"
    else:
        url = API_URL + "/fp-api/startrack/get-label/"

    data = {}
    data["booking_id"] = booking["id"]
    headers = {"Authorization": f"JWT {token}"}
    response = requests.post(url, json=data, headers=headers)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)


def do_process(mysqlcon, token):
    # Get 3 ST bookings
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to process(BOOK & LABEL): ", len(bookings))

    if len(bookings) > 0:
        time.sleep(5)

        for booking in bookings:
            print("#200 - Processing: ***", booking["b_bookingID_Visual"], "***")
            result = do_book(booking, token)

            if "message" in result and "Successfully booked" in result["message"]:
                do_create_and_get_label(booking, token)

    # Get 3 ST bookings
    bookings = get_bookings(mysqlcon, "missing-label")
    print("#200 - Booking cnt to process(LABEL-ONLY): ", len(bookings))

    if len(bookings) > 0:
        time.sleep(5)

        for booking in bookings:
            do_create_and_get_label(booking, token)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())
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
    except:
        print("Mysql DB connection error!")
        exit(1)

    try:
        option = get_option(mysqlcon, "st_auto_book_label")

        if int(option["option_value"]) == 0:
            print("#905 - `st_auto_book_label` option is OFF")
        elif option["is_running"]:
            print("#905 - `st_auto_book_label` script is already RUNNING")
        else:
            print("#906 - `st_auto_book_label` option is ON")
            set_option(mysqlcon, "st_auto_book_label", True)
            print("#910 - Processing...")
            token = get_token()
            do_process(mysqlcon, token)
            set_option(mysqlcon, "st_auto_book_label", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "st_auto_book_label", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
