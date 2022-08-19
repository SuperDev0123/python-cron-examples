# Python 3

from openpyxl import load_workbook
from collections import OrderedDict
import pymysql, pymysql.cursors
import sys
import os
import errno
import shutil
import datetime
import uuid

# production = False  # Local
production = True  # Prod

if production:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"  # New db
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


def do_process(fpath, mysqlcon):
    wb = load_workbook(filename=fpath, data_only=True)
    worksheet0 = wb["Sheet1"]

    first_row = None
    last_row = len(worksheet0["A0"])

    if worksheet0["A1"].value == "Booked Date":
        first_row = 2
    elif worksheet0["A2"].value == "Booked Date":
        first_row = 3

    for row_index in range(first_row, last_row + 1):
        status_history_feedback = worksheet0["L%i" % row_index].value
        v_FPBookingNumber = worksheet0["G%i" % row_index].value
        print("@903 - ", v_FPBookingNumber, status_history_feedback)

        # Update DB
        with mysqlcon.cursor() as cursor:
            sql = "SELECT dme_status_history_notes \
                    FROM `dme_bookings` \
                    WHERE v_FPBookingNumber =%s"
            cursor.execute(sql, (v_FPBookingNumber))
            booking = cursor.fetchone()

            if booking["dme_status_history_notes"]:
                sql = "UPDATE `dme_bookings` \
                        SET dme_status_history_notes=CONCAT(dme_status_history_notes, %s) \
                        WHERE v_FPBookingNumber=%s"
            else:
                sql = "UPDATE `dme_bookings` \
                        SET dme_status_history_notes=%s \
                        WHERE v_FPBookingNumber=%s"

            cursor.execute(sql, (status_history_feedback, v_FPBookingNumber))
            mysqlcon.commit()
    print("#902 - Processed %s lines" % (last_row - first_row + 1))


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
        if production:
            XLS_DIR = "/home/cope_au/dme_sftp/dme/status_history_feedback/indata/"
            XLS_ARCHIVE_DIR = (
                "/home/cope_au/dme_sftp/dme/status_history_feedback/archive/"
            )
        else:
            XLS_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
            XLS_ARCHIVE_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

        for fname in os.listdir(XLS_DIR):
            fpath = os.path.join(XLS_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".xlsx"):
                print("#901 - Detected .xlsx file:", fname)
                do_process(fpath, mysqlcon)
                shutil.move(XLS_DIR + fname, XLS_ARCHIVE_DIR + fname)

    except OSError as e:
        print(str(e))

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
