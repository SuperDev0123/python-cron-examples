# Python 3.7

import sys
import os
import errno
import shutil
import datetime
import uuid
import requests
import json
import traceback
import pymysql, pymysql.cursors
import xlsxwriter as xlsxwriter
from openpyxl import load_workbook

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def _update_bookingSet_status(bookingSet_id, status, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "UPDATE dme_booking_sets \
        SET status=%s \
        WHERE id=%s"
    cursor.execute(sql, (status, bookingSet_id))
    mysqlcon.commit()


def _get_bookings(booking_ids, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = f"SELECT * FROM dme_bookings WHERE id in ({booking_ids})"
    cursor.execute(sql)
    bookings = cursor.fetchall()
    return bookings


def _get_bookingSets_to_get_pricing(mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "SELECT * \
        FROM dme_booking_sets \
        WHERE status=%s OR status=%s"
    cursor.execute(sql, ("Created", "Pricing again"))
    bookingSets = cursor.fetchall()
    return bookingSets


def _pricing(booking, auto_select_type):
    url = API_URL + "/fp-api/pricing/"
    data = {"booking_id": booking["id"], "auto_select_type": auto_select_type}
    response = requests.post(url, params={}, json=data)

    try:
        # print(f"@200 - {response.status_code}")

        if response.status_code == 200:
            response0 = response.content.decode("utf8")
            data0 = json.loads(response0)
            # s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
            # print(f"@210 - Pricing result: {s0}")
            if len(data0["results"]) > 0:
                return True

        return False
    except Exception as e:
        print(f"@400, {str(e)}")
        return False


def do_process(mysqlcon):
    print(f"#800 - Retrieving BookingSets...")
    bookingSets = _get_bookingSets_to_get_pricing(mysqlcon)

    if bookingSets:
        print(f"#801 - BookingSets count:", len(bookingSets))
        bookingSet = bookingSets[0]
        _update_bookingSet_status(
            bookingSet["id"], f"In Progress(Pricing) {0}%", mysqlcon
        )
        print(f"#802 - Retrieving Bookings...")
        bookings = _get_bookings(bookingSet["booking_ids"], mysqlcon)

        if bookings:
            print(f"#803 - Bookings count:", len(bookings))
            success_cnt = 0

            for index, booking in enumerate(bookings):
                result = _pricing(booking, bookingSet["auto_select_type"])

                success_cnt = success_cnt + (1 if result else 0)
                print(f"#810 - Processing {index + 1}/{len(bookings)}")

                if index > 1:
                    _update_bookingSet_status(
                        bookingSet["id"],
                        f"In Progress(Pricing) {index / len(bookings) * 100}%",
                        mysqlcon,
                    )

            if success_cnt > 1:
                _update_bookingSet_status(
                    bookingSet["id"],
                    f"Completed(Pricing): {success_cnt} / {len(bookings)} Bookings have pricing info, {len(bookings) - success_cnt} / {len(bookings)} do not have pricing info",
                    mysqlcon,
                )
            else:
                _update_bookingSet_status(
                    bookingSet["id"],
                    f"Completed(Pricing): {0} / {len(bookings)} Bookings have pricing info",
                    mysqlcon,
                )
        else:
            print(f"#899 - No Bookings!")
    else:
        print(f"#899 - No BookingSets to get pricing!")


if __name__ == "__main__":
    print("#900 Started %s" % datetime.datetime.now())
    set_option(mysqlcon, "auto_pricing_set", True)

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
        option = get_option(mysqlcon, "auto_pricing_set")

        if int(option["option_value"]) == 0:
            print("#905 - `auto_pricing_set` option is OFF")
        elif option["is_running"]:
            print("#905 - `auto_pricing_set` script is already RUNNING")
        else:
            print("#906 - `auto_pricing_set` option is ON")
            print("#910 - Processing...")
            do_process(mysqlcon)
    except Exception as e:
        print("#904 Error: ", str(e))

    mysqlcon.close()
    set_option(mysqlcon, "auto_pricing_set", False)
    print("#999 Finished %s" % datetime.datetime.now())
