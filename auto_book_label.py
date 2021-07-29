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

TYPE_1 = 1  # Plum
TYPE_2 = 2  # JasonL


def get_token():
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


def get_bookings(mysqlcon, type):
    with mysqlcon.cursor() as cursor:
        if type == TYPE_1:  # Plum
            sql = "SELECT `id`, `b_bookingID_Visual`, `vx_freight_provider`, `kf_client_id` \
                    FROM `dme_bookings` \
                    WHERE `b_dateBookedDate` is NULL and `b_status`=%s and `kf_client_id`=%s and \
                    (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                    ORDER BY id DESC \
                    LIMIT 10"
            cursor.execute(
                sql, ("Ready for Booking", "461162D2-90C7-BF4E-A905-000000000004", "")
            )
            bookings = cursor.fetchall()
        elif type == TYPE_2:  # JasonL
            sql = "SELECT `id`, `b_bookingID_Visual`, `vx_freight_provider`, `kf_client_id` \
                    FROM `dme_bookings` \
                    WHERE `b_status`=%s and `kf_client_id`=%s \
                    ORDER BY id DESC \
                    LIMIT 10"
            cursor.execute(
                sql, ("Ready for Despatch", "1af6bcd2-6148-11eb-ae93-0242ac130002")
            )
            bookings = cursor.fetchall()

        return bookings


def reset_booking(mysqlcon, booking):
    with mysqlcon.cursor() as cursor:
        # JasonL & TNT
        if booking["kf_client_id"] == "1af6bcd2-6148-11eb-ae93-0242ac130002":
            sql = "UPDATE `dme_bookings` \
                    SET `v_FPBookingNumber`=NULL, `b_status`=%s, `b_dateBookedDate`=NULL, `b_error_Capture`=%s \
                    WHERE id=%s"
            cursor.execute(
                sql, ("Ready for Despatch", "Error while BOOK on TNT.", booking["id"])
            )
            mysqlcon.commit()


def do_book(booking, token):
    if not booking["vx_freight_provider"].lower() in ["century"]:  # Via FP API
        url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/book/"
        data = {"booking_id": booking["id"]}
        response = requests.post(url, params={}, json=data)
        response0 = response.content.decode("utf8")
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
        print("@210 - BOOK (via FP API) result: ", s0)
        return data0
    else:  # Via CSV
        url = API_URL + f"/get-csv/"
        data = {
            "bookingIds": [booking["id"]],
            "vx_freight_provider": booking["vx_freight_provider"],
        }
        headers = {"Authorization": f"JWT {token}"}
        response = requests.post(url, params={}, json=data, headers=headers)
        response0 = response.content.decode("utf8")
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
        print("@211 - BOOK (via CSV) result: ", s0)
        return data0


def do_get_label(booking):
    url = API_URL + f"/fp-api/{booking['vx_freight_provider'].lower()}/get-label/"
    data = {"booking_id": booking["id"]}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - LABEL result: ", s0)
    return data0


def do_process(mysqlcon):
    token = get_token()

    # bookings = get_bookings(mysqlcon, TYPE_1)  # Plum
    # print("#200 - Booking cnt to process(Plum): ", len(bookings))

    # if len(bookings) > 0:
    #     for booking in bookings:
    #         print("#201 - Processing: ***", booking["b_bookingID_Visual"], "***")
    #         result = do_book(booking)

    #         if (
    #             {booking["vx_freight_provider"].lower()} not in ["hunter", "capital"]
    #             and "message" in result
    #             and "Successfully booked" in result["message"]
    #         ):
    #             do_get_label(booking)

    bookings = get_bookings(mysqlcon, TYPE_2)  # JasonL
    print("#202 - Booking cnt to process(JasonL): ", len(bookings))

    if len(bookings) > 0:
        for booking in bookings:
            print("#203 - Processing: ***", booking["b_bookingID_Visual"], "***")
            result = do_book(booking, token)

            if (
                booking["vx_freight_provider"].lower() == "tnt"
                and "message" in result
                and "Successfully booked" in result["message"]
            ):
                label_result = do_get_label(booking)

                if "Successfully" not in result.get("message"):
                    reset_booking(booking, mysqlcon)


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
