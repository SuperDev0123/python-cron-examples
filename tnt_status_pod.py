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


def get_option(mysqlcon, flag_name):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_options` \
                WHERE option_name=%s"
        cursor.execute(sql, (flag_name))
        dme_option = cursor.fetchone()

        return dme_option


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `vx_freight_provider`=%s and `z_api_issue_update_flag_500`=%s and \
                (`b_status` is NULL or (`b_status`<>%s and `b_status`<>%s)) and \
                (`b_error_Capture` is NULL or `b_error_Capture`=%s) \
                ORDER BY id DESC \
                LIMIT 200"
        cursor.execute(sql, ("TNT", "1", "Ready for booking", "Delivered", ""))
        bookings = cursor.fetchall()

        return bookings


def get_bookings_missing_pod(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `b_error_Capture` \
                FROM `dme_bookings` \
                WHERE `vx_freight_provider`=%s and b_status=%s and z_pod_url is NULL \
                ORDER BY id DESC \
                LIMIT 20"
        cursor.execute(sql, ("TNT", "Delivered"))
        bookings = cursor.fetchall()

        return bookings


def do_tracking(booking):
    url = API_URL + "/fp-api/tnt/tracking/"
    data = {"booking_id": booking["id"]}

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    try:
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
        print("@210 - Tracking result:", s0)
    except Exception as e:
        print("@410 - Tracking error:", str(e))
        pass

    return data0


def do_pod(booking):
    url = API_URL + "/fp-api/tnt/pod/"
    data = {"booking_id": booking["id"]}

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    # s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    # print("@210 - POD result:", s0)
    return data0


def do_process(mysqlcon):
    # Get 200 TNT bookings
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to process: ", len(bookings))

    for booking in bookings:
        print("#201 - Processing: ***", booking["b_bookingID_Visual"], "***")
        result = do_tracking(booking)

        if "b_status" in result and result["b_status"] == "Delivered":
            do_pod(booking)

    # Get 20 TNT bookings that b_status is `Delivered` but missed POD
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
        option = get_option(mysqlcon, "tnt_status_pod")

        if int(option["option_value"]) == 0:
            print("#905 - `tnt_status_pod` option is OFF")
        else:
            print("#906 - `tnt_status_pod` option is ON")
            do_process(mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
