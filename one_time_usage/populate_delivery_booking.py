# Python 3.7.0
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


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, b_bookingID_Visual, pk_booking_id \
                FROM `dme_bookings` \
                WHERE `kf_client_id`<>%s and `b_status`='Delivered' and delivery_booking is null \
                ORDER BY id DESC"
        cursor.execute(sql, ("7EAA4B16-484B-3944-902E-BC936BFEF535"))
        bookings = cursor.fetchall()

        return bookings


def get_status_histories(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, fk_booking_id, status_last, z_createdTimeStamp, event_time_stamp \
                FROM `dme_status_history` \
                WHERE `fk_booking_id`=%s and (status_last='Shipment has been delivered.' or status_last='Delivered')\
                ORDER BY id DESC"
        cursor.execute(sql, (booking["pk_booking_id"]))
        status_history = cursor.fetchone()

        if status_history:
            print("@320 - ", booking["pk_booking_id"], status_history)
            return status_history
        else:
            print("@321 - Not found", booking["pk_booking_id"])

        return


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)
    print("@310 - Bookings Cnt:", len(bookings))

    with mysqlcon.cursor() as cursor:
        for booking in bookings:
            status_history = get_status_histories(booking, mysqlcon)

            if status_history and status_history["event_time_stamp"]:
                sql = "UPDATE dme_bookings \
                        SET delivery_booking=%s \
                        WHERE id=%s"
                cursor.execute(sql, (status_history["event_time_stamp"], booking["id"]))
                mysqlcon.commit()
            elif status_history and status_history["z_createdTimeStamp"]:
                sql = "UPDATE dme_bookings \
                        SET delivery_booking=%s \
                        WHERE id=%s"
                cursor.execute(
                    sql, (status_history["z_createdTimeStamp"], booking["id"])
                )
                mysqlcon.commit()


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
