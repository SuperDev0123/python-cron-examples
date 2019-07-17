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
    CSV_FILE_PATH = "/home/gold/chrons(not run here)/move_from_imgs_to_POD indata_rename_and process.csv"
    POD_FILE_DIR = "/var/www/html/dme_api/static/imgs/"
else:
    CSV_FILE_PATH = "/Users/admin/work/goldmine/scripts/dir01/move_from_imgs_to_POD indata_rename_and process.csv"


def update_booking(b_bookingID_Visual, fname, mysqlcon):
    with mysqlcon.cursor() as cursor:
        if "signed" in fname:
            sql = "UPDATE `dme_bookings` \
                SET `z_pod_signed_url`=%s, z_ModifiedTimestamp=%s \
                WHERE `b_bookingID_Visual`=%s"
            cursor.execute(sql, (fname, datetime.datetime.now(), b_bookingID_Visual))
            mysqlcon.commit()
        else:
            sql = "UPDATE `dme_bookings` \
                SET `z_pod_url`=%s, z_ModifiedTimestamp=%s \
                WHERE `b_bookingID_Visual`=%s"
            cursor.execute(sql, (fname, datetime.datetime.now(), b_bookingID_Visual))
            mysqlcon.commit()


def do_process(csv_lines, mysqlcon):
    count = 0
    for fname in sorted(os.listdir(POD_FILE_DIR)):
        fpath = os.path.join(POD_FILE_DIR, fname)

        for csv_line in csv_lines:
            if str(csv_line) in str(fname):
                update_booking(csv_line, fname, mysqlcon)
                count += 1

    print(f"@905 - {count} bookings updated")


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

    if not os.path.isfile(CSV_FILE_PATH):
        print('Given argument "%s" is not a directory' % CSV_FILE_PATH)
        exit(1)

    csv_lines = []

    with open(CSV_FILE_PATH) as csv_file:
        for line in list(csv_file):
            csv_lines.append(line[:-1])

    try:
        if len(csv_lines) > 0:
            do_process(csv_lines, mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
