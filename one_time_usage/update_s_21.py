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


def update_s_21(fpath, mysqlcon):
    with open(fpath) as csv_file:
        with mysqlcon.cursor() as cursor:
            for i, line in enumerate(csv_file):
                v_FPBookingNumber = line.split(",")[0]
                b_status_API_csv = line.split(",")[1]
                b_fp_qty_delivered_csv = line.split(",")[2]

                if "-" in line.split(",")[3]:
                    event_time_stamp = datetime.datetime.strptime(
                        line.split(",")[3] + " " + line.split(",")[4].replace("\n", ""),
                        "%Y-%m-%d %H:%M",
                    )
                else:
                    event_time_stamp = datetime.datetime.strptime(
                        line.split(",")[3] + " " + line.split(",")[4].replace("\n", ""),
                        "%d/%m/%y %H:%M",
                    )

                if b_status_API_csv == '"Proof of Delivery"':
                    print(
                        f"@200 - index: {i}: v_FPBookingNumber: {v_FPBookingNumber} event_time_stamp: {event_time_stamp}"
                    )
                    sql = "UPDATE `dme_bookings` \
                        SET s_21_Actual_Delivery_TimeStamp=%s \
                        WHERE `v_FPBookingNumber`=%s"
                    cursor.execute(sql, (event_time_stamp, v_FPBookingNumber))
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

    if production:
        CSV_DIR = "/home/gold/chrons(not run here)/files_to_process/"
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
                update_s_21(fpath, mysqlcon)
    except OSError as e:
        print("#902 Error", str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
