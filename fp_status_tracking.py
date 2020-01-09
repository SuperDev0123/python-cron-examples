# Python 3.6.6
# V 1.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

import _status_history

IS_DEBUG = False
# IS_PRODUCTION = True  # Dev
IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
    # DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = ""
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    # API_URL = "http://3.105.62.128/api"  # Dev
    API_URL = "http://13.55.64.102/api"  # Prod
else:
    API_URL = "http://localhost:8000/api"  # Local

FP_NAMES = ["TNT", "HUNTER"]


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = f"SELECT `id`, `pk_booking_id`, `b_bookingID_Visual`, `vx_freight_provider`, `b_status`, `b_status_API` \
                FROM `dme_bookings` \
                WHERE UPPER(`vx_freight_provider`) in {str(tuple(FP_NAMES))} AND `b_dateBookedDate` IS NOT NULL \
                    AND `b_status`<>%s AND `b_status`<>%s \
                ORDER BY id DESC \
                LIMIT 100"
        cursor.execute(sql, ("Ready for booking", "Delivered"))
        bookings = cursor.fetchall()

        return bookings


def _set_error(booking, error, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
                SET b_error_Capture=%s, z_ModifiedTimestamp=%s \
                WHERE id=%s"
        cursor.execute(sql, (error, datetime.datetime.now(), booking["id"]))
        mysqlcon.commit()


def get_tracking_info(booking, mysqlcon):
    url = f"{API_URL}/fp-api/{booking['vx_freight_provider']}/tracking/"
    data = {}
    data["booking_id"] = booking["id"]

    response0 = requests.post(url, params={}, json=data)
    response0 = response0.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)
    return data0


def do_process(mysqlcon):
    # Get 3 ST bookings
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to Tracking: ", len(bookings))

    if len(bookings) > 0:
        for booking in bookings:
            print(
                f"#201 - Processing: ({booking['b_bookingID_Visual']} - {booking['vx_freight_provider']})"
            )
            tracking_info = get_tracking_info(booking, mysqlcon)

            if "error" in tracking_info:
                _set_error(booking, tracking_info["error"], mysqlcon)
            elif "message" in tracking_info:
                new_b_status_API = tracking_info["message"]

                # if booking["b_status_API"] != new_b_status_API:
                #     _status_history.create(
                #         booking["id"], new_b_status_API, event_time_stamp
                #     )


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

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
