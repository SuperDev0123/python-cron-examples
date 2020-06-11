# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = "dme_db_dev"  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    # API_URL = "http://3.105.62.128/api"  # Dev
    API_URL = "http://13.55.64.102/api"  # Prod
else:
    API_URL = "http://localhost:8000/api"  # Local


def get_bookings(mysqlcon, type="not-booked"):
    with mysqlcon.cursor() as cursor:
        if type == "not-booked":
            sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                    FROM `dme_bookings` \
                    WHERE `vx_freight_provider`=%s and `b_dateBookedDate` is NULL and `b_status`=%s and \
                    (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                    ORDER BY id DESC \
                    LIMIT 3"
            cursor.execute(sql, ("StarTrack", "Ready for Booking", ""))
        elif type == "missing-label":
            sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                    FROM `dme_bookings` \
                    WHERE `vx_freight_provider`=%s and `b_dateBookedDate` is not NULL and `b_status`=%s and \
                    `z_label_url` is NULL and z_CreatedTimestamp > '2020-01-01' and \
                    (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                    ORDER BY id DESC \
                    LIMIT 10"
            cursor.execute(sql, ("StarTrack", "Booked", ""))
        bookings = cursor.fetchall()

        return bookings


def do_book(booking):
    url = API_URL + "/fp-api/startrack/book/"
    data = {}
    data["booking_id"] = booking["id"]

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - ", s0)
    return data0


def do_create_and_get_label(booking):
    url = API_URL + "/fp-api/startrack/get-label/"
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
    print("#200 - Booking cnt to process(BOOK & LABEL): ", len(bookings))

    if len(bookings) > 0:
        time.sleep(5)

        for booking in bookings:
            print("#200 - Processing: ***", booking["b_bookingID_Visual"], "***")
            result = do_book(booking)

            if "message" in result and "Successfully booked" in result["message"]:
                do_create_and_get_label(booking)

    # Get 3 ST bookings
    bookings = get_bookings(mysqlcon, "missing-label")
    print("#200 - Booking cnt to process(LABEL-ONLY): ", len(bookings))

    if len(bookings) > 0:
        time.sleep(5)

        for booking in bookings:
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

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
