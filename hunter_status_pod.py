# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def get_in_progress_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `vx_freight_provider`=%s \
                    AND (`b_client_name`=%s OR `b_client_name`=%s OR `b_client_name`=%s) \
                    AND (`z_lock_status`=%s OR `z_lock_status` IS NULL) \
                    AND (`b_status`<>%s AND `b_status`<>%s AND `b_status`<>%s AND `b_status`<>%s) \
                ORDER BY id DESC \
                LIMIT 200"
        cursor.execute(
            sql,
            (
                "Hunter",
                "Tempo Pty Ltd",
                "Plum Products Australia Ltd",
                "Reworx",
                "0",
                "Ready for booking",
                "Cancelled",
                "Closed",
                "Delivered",
            ),
        )
        bookings = cursor.fetchall()

        return bookings


def get_bookings_missing_pod(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `vx_freight_provider`=%s AND `b_client_name`=%s AND z_pod_url IS NULL \
                    AND (`z_lock_status`=%s OR `z_lock_status` IS NULL) \
                    AND `b_status`=%s \
                ORDER BY id DESC \
                LIMIT 20"
        cursor.execute(sql, ("Hunter", "Tempo Pty Ltd", "0", "Delivered"))
        bookings = cursor.fetchall()

        return bookings


def do_tracking(booking):
    url = API_URL + "/fp-api/hunter/tracking/"
    data = {"booking_id": booking["id"]}

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - Tracking result:", s0)
    return data0


def do_pod(booking):
    url = API_URL + "/fp-api/hunter/pod/"
    data = {"booking_id": booking["id"]}

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - POD result:", s0)
    return data0


def do_process(mysqlcon):
    # Get 200 Hunter bookings
    bookings = get_in_progress_bookings(mysqlcon)
    print("#200 - Booking cnt to process: ", len(bookings))

    if len(bookings) > 0:
        for booking in bookings:
            time.sleep(10)
            print("#200 - Processing: ***", booking["b_bookingID_Visual"], "***")
            result = do_tracking(booking)

            if "b_status" in result and result["b_status"] == "Delivered":
                do_pod(booking)

    # Get 20 Hunter bookings that b_status is `Delivered` but missed POD
    bookings = get_bookings_missing_pod(mysqlcon)
    print("#210 - Booking(missing POD) cnt to process: ", len(bookings))

    for booking in bookings:
        print("#211 - Processing: ***", booking["b_bookingID_Visual"], "***")
        counter = 0
        result = None

        while counter < 3:
            result = do_pod(booking)

            if "message" in result and "successfully" in result["message"]:
                break

            counter += 1
            time.sleep(10)


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
        option = get_option(mysqlcon, "hunter_status_pod")

        if int(option["option_value"]) == 0:
            print("#905 - `hunter_status_pod` option is OFF")
        elif option["is_running"]:
            print("#905 - `hunter_status_pod` script is already RUNNING")
        else:
            print("#906 - `hunter_status_pod` option is ON")
            set_option(mysqlcon, "hunter_status_pod", True)
            do_process(mysqlcon)
            set_option(mysqlcon, "hunter_status_pod", False, time1)
    except OSError as e:
        set_option(mysqlcon, "hunter_status_pod", False, time1)
        print("Error:", str(e))

    mysqlcon.close()
    print("#909 - Finished %s" % datetime.datetime.now())
