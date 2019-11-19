# Python 3.6.6

import sys, time
import os
import errno
import datetime
import uuid
import urllib, requests
import json
import pymysql, pymysql.cursors
import base64
import shutil

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = 'dme_db_dev'  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def get_v_FPBookingNumber(v_FPBookingNumber):
    # if "_" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("_", "")
    # if "-" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("-", "")

    return v_FPBookingNumber


def get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (v_FPBookingNumber))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result


def do_process(fpath, mysqlcon):
    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            v_FPBookingNumber = get_v_FPBookingNumber(line.split(",")[0])
            fp_store_event_date = datetime.datetime.strptime(
                line.split(",")[2], "%Y-%m-%d"
            )
            fp_store_event_time = datetime.datetime.strptime(
                line.split(",")[3].replace("\n", ""), "%H:%M"
            )
            booking = get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon)

            if booking:
                print("@103 v_FPBookingNumber match: ", v_FPBookingNumber, date)
                with mysqlcon.cursor() as cursor:
                    sql = "UPDATE `dme_bookings` \
                           SET de_Deliver_From_Date=%s, de_Deliver_By_Date=%s, fp_store_event_date=%s, fp_store_event_time=%s \
                           WHERE id=%s"
                    cursor.execute(
                        sql,
                        (
                            fp_store_event_date,
                            fp_store_event_date,
                            fp_store_event_date,
                            fp_store_event_time,
                            booking["id"],
                        ),
                    )
                    mysqlcon.commit()
            else:
                print("@104 v_FPBookingNumber not match: ", v_FPBookingNumber)


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

    if production:
        CSV_DIR = "/home/cope_au/dme_sftp/cope_au/store_bookings/indata/"
        ARCHIVE_DIR = "/home/cope_au/dme_sftp/cope_au/store_bookings/archive/"
    else:
        CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
        ARCHIVE_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

    if not os.path.isdir(CSV_DIR):
        print('Given argument "%s" is not a directory' % CSV_DIR)
        exit(1)

    try:
        for fname in os.listdir(CSV_DIR):
            fpath = os.path.join(CSV_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".csv"):
                print("@100 Detect csv file:", fpath)
                do_process(fpath, mysqlcon)
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print("@109 Moved csv file:", fpath)

    except OSError as e:
        print(str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
