# Python 3.7.0
# V 1.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors

from _tempo_push_booking import push_via_api

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


def get_booking(mysqlcon, booking_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_bookings` \
                WHERE id=%s"
        cursor.execute(sql, (booking_id))
        booking = cursor.fetchone()

        return booking


def get_option(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_options` \
                WHERE option_name=%s"
        cursor.execute(sql, ("tempo_push"))
        dme_option = cursor.fetchone()

        return dme_option


def create(booking_id, new_b_status_API, event_time_stamp, new_b_status=None):
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

    booking = get_booking(mysqlcon, booking_id)

    with mysqlcon.cursor() as cursor:
        if not new_b_status:
            sql = "SELECT `dme_status` \
                    FROM `dme_utl_fp_statuses` \
                    WHERE fp_lookup_status=%s"
            cursor.execute(sql, (new_b_status_API))
            result = cursor.fetchone()
            b_status = result["dme_status"]
        else:
            b_status = new_b_status

        sql = "INSERT INTO `dme_status_history` \
                (`fk_booking_id`, `status_old`, `notes`, `status_last`, \
                 `z_createdTimeStamp`, `event_time_stamp`, `recipient_name`, `status_update_via`, \
                 `b_booking_visualID` ) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(
            sql,
            (
                booking["pk_booking_id"],
                booking["b_status"],
                str(booking["b_status"]) + " ---> " + str(b_status),
                b_status,
                datetime.datetime.now(),
                datetime.datetime.now()
                if event_time_stamp == "null"
                else event_time_stamp,
                " ",
                "fp api",
                booking["b_bookingID_Visual"],
            ),
        )
        mysqlcon.commit()

        sql = "UPDATE `dme_bookings` \
                SET b_status=%s \
                WHERE id=%s"
        cursor.execute(sql, (b_status, booking["id"]))
        mysqlcon.commit()

        option = get_option()
        if (
            booking["kf_client_id"] == "461162D2-90C7-BF4E-A905-092A1A5F73F3"
            and int(option["option_value"]) == 1
        ):
            push_via_api(booking)
