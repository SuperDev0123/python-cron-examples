# Python 3.7

import sys
import os
import datetime
import requests
import json
import traceback
import time
import pymysql, pymysql.cursors

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


def _update_bookingSet_status(bookingSet_id, status, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "UPDATE dme_booking_sets SET status=%s WHERE id=%s"
    cursor.execute(sql, (status, bookingSet_id))
    mysqlcon.commit()


def _update_booking_error(booking, error, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "UPDATE dme_bookings SET b_error_Capture=%s WHERE id=%s"
    cursor.execute(sql, (error, booking["id"]))
    mysqlcon.commit()


def _get_booked_cnt(booking_ids, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = (
        "SELECT id, b_bookingID_Visual, b_dateBookedDate, vx_freight_provider, api_booking_quote_id "
        + f'FROM dme_bookings WHERE id in ({booking_ids}) and b_status="Booked"'
    )
    cursor.execute(sql)
    bookings = cursor.fetchall()
    return len(bookings)


def _get_label_built_cnt(booking_ids, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = (
        "SELECT id "
        + f"FROM dme_bookings WHERE id in ({booking_ids}) and z_label_url IS NOT NULL"
    )
    cursor.execute(sql)
    bookings = cursor.fetchall()
    return len(bookings)


def _get_bookings(booking_ids, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = (
        "SELECT id, b_bookingID_Visual, b_dateBookedDate, vx_freight_provider, api_booking_quote_id, b_client_name "
        + f"FROM dme_bookings WHERE id in ({booking_ids})"
    )
    cursor.execute(sql)
    bookings = cursor.fetchall()
    return bookings


def _get_bookingSets_to_process(mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "SELECT * FROM dme_booking_sets WHERE status=%s OR status=%s"
    cursor.execute(sql, ("Starting BOOK", "Build Label again"))
    bookingSets = cursor.fetchall()
    return bookingSets


def do_book(booking):
    url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/book/"
    data = {"booking_id": booking["id"]}
    response = requests.post(url, params={}, json=data)

    try:
        # print(f"@200 - {response.status_code}")

        if response.status_code == 200:
            response0 = response.content.decode("utf8")
            data0 = json.loads(response0)
            # s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
            # print(f"@210 - Pricing result: {s0}")
            if len(data0["message"]) > 0:
                return data0

        return None
    except Exception as e:
        print(f"@400, {str(e)}")
        return None


def do_create_and_get_label(booking, token):
    if booking["b_client_name"] == "Tempo Big W":
        url = API_URL + f"/build-label/"
    else:
        url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/get-label/"
    data = {"booking_id": booking["id"]}
    headers = {"Authorization": "JWT " + token, "Content-Type": "application/json"}
    response = requests.post(url, params={}, json=data, headers=headers)

    try:
        print(f"@200 - {response.status_code}")

        if response.status_code == 200:
            response0 = response.content.decode("utf8")
            data0 = json.loads(response0)
            s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
            print(f"@210 - Pricing result: {s0}")

            if len(data0["message"]) > 0:
                return data0

        return None
    except Exception as e:
        print(f"@401, {str(e)}")
        return None


def do_process(mysqlcon):
    print(f"#800 - Retrieving BookingSets...")
    bookingSets = _get_bookingSets_to_process(mysqlcon)

    if bookingSets:
        print(f"#801 - BookingSets count:", len(bookingSets))
        bookingSet = bookingSets[0]
        progress = "BOOK" if bookingSet["status"] == "Starting BOOK" else "LABEL"
        _update_bookingSet_status(
            bookingSet["id"], f"In Progress({progress}) {0}%", mysqlcon
        )
        print(f"#802 - Retrieving Bookings...")
        bookings = _get_bookings(bookingSet["booking_ids"], mysqlcon)

        if bookings:
            print(f"#803 - Bookings count:", len(bookings))
            success_cnt = 0
            token = get_token()

            for index, booking in enumerate(bookings):
                print(
                    f"#810 - {progress} Processing {index + 1}/{len(bookings)} - {booking['b_bookingID_Visual']}, {booking['vx_freight_provider']}, Pricing<{booking['api_booking_quote_id']}>"
                )

                try:
                    if progress == "BOOK" and booking["b_dateBookedDate"]:
                        pass
                    elif (
                        booking["vx_freight_provider"]
                        and booking["api_booking_quote_id"]
                    ):
                        if progress == "BOOK":
                            _update_bookingSet_status(
                                bookingSet["id"],
                                f"In Progress(BOOK) {index / len(booking) * 100}%",
                                mysqlcon,
                            )
                            result = do_book(booking)

                            if (
                                result
                                and "message" in result
                                and "Successfully booked" in result["message"]
                                and not booking["vx_freight_provider"].lower()
                                in ["capital", "hunter"]
                            ):
                                _update_bookingSet_status(
                                    bookingSet["id"],
                                    f"In Progress(LABEL) {index / len(booking) * 100}%",
                                    mysqlcon,
                                )
                                do_create_and_get_label(booking, token)
                        else:
                            _update_bookingSet_status(
                                bookingSet["id"],
                                f"In Progress(LABEL) {index / len(booking) * 100}%",
                                mysqlcon,
                            )
                            do_create_and_get_label(booking, token)
                    else:
                        msg = "Pricing is not selected!"
                        print("#840 - ", msg)
                        _update_booking_error(booking, msg, mysqlcon)
                except Exception as e:
                    print(f"@591 - Error: {e}")
                    pass

            booked_cnt = (
                _get_booked_cnt(bookingSet["booking_ids"], mysqlcon)
                if progress == "BOOK"
                else _get_label_built_cnt(bookingSet["booking_ids"], mysqlcon)
            )
            _update_bookingSet_status(
                bookingSet["id"],
                f"Completed(BOOK): {booked_cnt} / {len(bookings)} Bookings have been Booked"
                if progress == "BOOK"
                else f"Completed(LABEL): {booked_cnt} / {len(bookings)} Labels have been Built",
                mysqlcon,
            )
        else:
            print(f"#899 - No Bookings!")
    else:
        print(f"#899 - No BookingSets to BOOK!")


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
        option = get_option(mysqlcon, "auto_book_label_set")

        if int(option["option_value"]) == 0:
            print("#905 - `auto_book_label_set` option is OFF")
        elif option["is_running"]:
            print("#905 - `auto_book_label_set` script is already RUNNING")
        else:
            print("#906 - `auto_book_label_set` option is ON")
            time1 = time.time()
            set_option(mysqlcon, "auto_book_label_set", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "auto_book_label_set", False, time1)
    except Exception as e:
        print("#904 Error: ", str(e))
        set_option(mysqlcon, "auto_book_label_set", False, time1)

    mysqlcon.close()
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())
