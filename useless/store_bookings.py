# Python 3.6.6

import sys, time
import os
import datetime
import json
import pymysql, pymysql.cursors
import shutil

production = True  # Dev
# production = False  # Local

if production:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = "dme_db_dev"  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = ""
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


def do_process(fpath, fname, mysqlcon):
    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            v_FPBookingNumber = get_v_FPBookingNumber(line.split(",")[0])
            new_delivery_booking = (
                datetime.datetime.strptime(line.split(",")[1], "%Y-%m-%d")
                if "No" not in line.split(",")[1]
                else None
            )
            new_fp_store_event_date = datetime.datetime.strptime(
                line.split(",")[2], "%Y-%m-%d"
            )
            new_fp_store_event_time = datetime.datetime.strptime(
                line.split(",")[3].replace("\n", ""), "%H:%M"
            )

            new_fp_store_event_desc = ""
            if len(line.split(",")) > 4:
                new_fp_store_event_desc = line.split(",")[4]

            booking = get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon)

            if booking:
                print(
                    f"@103 v_FPBookingNumber match: {v_FPBookingNumber},    OLD: {booking['delivery_booking']}, {booking['fp_store_event_date']},    NEW: {new_delivery_booking}, {new_fp_store_event_date}"
                )
                with mysqlcon.cursor() as cursor:
                    if not booking["fp_store_event_date"]:
                        sql = "UPDATE `dme_bookings` \
                                SET delivery_booking=%s, de_Deliver_From_Date=%s, de_Deliver_By_Date=%s, \
                                    fp_store_event_date=%s, fp_store_event_time=%s \
                                WHERE v_FPBookingNumber=%s"
                        cursor.execute(
                            sql,
                            (
                                new_delivery_booking,
                                new_delivery_booking,
                                new_delivery_booking,
                                new_fp_store_event_date,
                                new_fp_store_event_time,
                                booking["v_FPBookingNumber"],
                            ),
                        )
                    if new_delivery_booking:
                        sql = "UPDATE `dme_bookings` \
                                SET delivery_booking=%s, de_Deliver_From_Date=%s, de_Deliver_By_Date=%s \
                                WHERE v_FPBookingNumber=%s"
                        cursor.execute(
                            sql,
                            (
                                new_delivery_booking,
                                new_delivery_booking,
                                new_delivery_booking,
                                booking["v_FPBookingNumber"],
                            ),
                        )

                    # Update Store event description anytime
                    sql = "UPDATE `dme_bookings` \
                            SET fp_store_event_desc=%s \
                            WHERE v_FPBookingNumber=%s"
                    cursor.execute(
                        sql, (new_fp_store_event_desc, booking["v_FPBookingNumber"])
                    )

                    sql = "INSERT INTO `fp_store_booking_log` \
                            (v_FPBookingNumber, delivery_booking, fp_store_event_date, \
                            fp_store_event_time, fp_store_event_desc, z_createdTimeStamp, csv_file_name) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(
                        sql,
                        (
                            v_FPBookingNumber,
                            new_delivery_booking,
                            new_fp_store_event_date,
                            new_fp_store_event_time,
                            new_fp_store_event_desc,
                            datetime.datetime.now(),
                            fname,
                        ),
                    )
                    mysqlcon.commit()
            else:
                print(f"@104 No Booking with {v_FPBookingNumber}")


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
        CSV_DIR = "./dir01/"
        ARCHIVE_DIR = "./dir02/"

    if not os.path.isdir(CSV_DIR):
        print('Given argument "%s" is not a directory' % CSV_DIR)
        exit(1)

    try:
        for fname in sorted(os.listdir(CSV_DIR)):
            fpath = os.path.join(CSV_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".csv"):
                print("@100 Detect csv file:", fpath)
                do_process(fpath, fname, mysqlcon)
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print("@109 Moved csv file:", fpath)

    except OSError as e:
        print(str(e))

    print("#901 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
