# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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
        sql = "SELECT `id`, `b_bookingID_Visual`, `v_FPBookingNumber` \
                From `dme_bookings` \
                WHERE `vx_freight_provider`=%s"
        cursor.execute(sql, ("Cope"))
        booking = cursor.fetchall()

        return booking


def update_booking(booking, z_first_scan_label_date, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
                SET `z_first_scan_label_date`=%s \
                WHERE `id`=%s"
        cursor.execute(sql, (z_first_scan_label_date, booking["id"]))
        mysqlcon.commit()


def process(fpath, bookings, mysqlcon):
    csv_lines = []

    with open(fpath) as csv_file:
        for line in reversed(list(csv_file)):
            csv_lines.append(line)

    for booking in bookings:
        for csv_line in csv_lines:
            if (
                booking["b_bookingID_Visual"]
                and str(booking["b_bookingID_Visual"]) in csv_line
            ):
                z_first_scan_label_date = (
                    datetime.datetime.strptime(csv_line.split(",")[2], "%Y-%m-%d"),
                )
                # print("@100 - ", booking["id"], csv_line, z_first_scan_label_date)
                update_booking(booking, z_first_scan_label_date, mysqlcon)
                break


if __name__ == "__main__":
    print("#900 - Started %s" % datetime.datetime.now())

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

    if IS_PRODUCTION:
        # CSV_FILE_PATH = "/home/cope_au/dme_sftp/cope_au/scans_labels/archive/scans-20190713180020.csv"
        CSV_FILE_PATH = (
            "/Users/admin/work/goldmine/scripts/dir01/scans-20190713180020.csv"
        )
    else:
        CSV_FILE_PATH = (
            "/Users/admin/work/goldmine/scripts/dir01/scans-20190713180020.csv"
        )

    if not os.path.isfile(CSV_FILE_PATH):
        print('Given argument "%s" is not a directory' % CSV_FILE_PATH)
        exit(1)

    bookings = get_bookings(mysqlcon)
    print("Cope bookings count:", len(bookings))

    try:
        process(CSV_FILE_PATH, bookings, mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
