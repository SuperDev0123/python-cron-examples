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
    DB_NAME = "dme_db_dev"  # Dev
    # DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    API_URL = "http://3.105.62.128/api"  # Dev
    # API_URL = "http://13.55.64.102/api"  # Prod
else:
    API_URL = "http://localhost:8000/api"  # Local


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `b_dateBookedDate` is NULL and `b_status`=%s and \
                `kf_client_id`=%s and `api_booking_quote_id` is NULL and \
                (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                ORDER BY id DESC"
        cursor.execute(
            sql, ("Ready for booking", "461162D2-90C7-BF4E-A905-000000000003", "")
        )
        bookings = cursor.fetchall()

        return bookings


def do_select_pricing(booking):
    url = API_URL + "/fp-api/pricing/"
    data = {}
    data["booking_id"] = booking["id"]

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@210 - Success")
    return data0


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to process: ", len(bookings))

    if len(bookings) > 0:
        for index, booking in enumerate(bookings):
            print(
                f"#201 - Processing({index}/{len(bookings)}): ***   {booking['b_bookingID_Visual']}   ***"
            )
            result = do_select_pricing(booking)


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

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
