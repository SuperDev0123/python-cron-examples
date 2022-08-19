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
    DB_PASS = ""
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def getBookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_booking_id`, `b_bookingID_Visual`, `vx_freight_provider`, `b_status`, `b_status_API` \
                FROM `dme_bookings` \
                WHERE (e_qty_scanned_fp_total=%s OR e_qty_scanned_fp_total IS NULL) and vx_freight_provider=%s"
        cursor.execute(sql, (0, "Cope"))
        results = cursor.fetchall()
        return results


def getBookingLines(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_booking_lines` \
                WHERE fk_booking_id = %s"
        cursor.execute(sql, (booking["pk_booking_id"]))
        results = cursor.fetchall()
        return results


def getApiBclCnt(booking, booking_line, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = f"SELECT * \
                FROM `api_booking_confirmation_lines` \
                WHERE fk_booking_id=%s AND fk_booking_line_id=%s"
        cursor.execute(sql, (booking["pk_booking_id"], booking_line["pk_lines_id"]))
        results = cursor.fetchall()
        return len(results)


def make_3digit(num):
    if num > 0 and num < 10:
        return "00" + str(num)
    elif num > 9 and num < 100:
        return "0" + str(num)
    elif num > 99 and num < 1000:
        return str(num)
    else:
        return str("ERROR: Number is bigger than 999")


def do_process(mysqlcon):
    bookings = getBookings(mysqlcon)
    print("@200 - Bookings Cnt:", len(bookings))

    for booking in bookings:
        booking_lines = getBookingLines(booking, mysqlcon)
        index = 1

        for booking_line in booking_lines:
            get_api_bcls_cnt = getApiBclCnt(booking, booking_line, mysqlcon)

            if get_api_bcls_cnt == 0:
                for i in range(int(booking_line["e_qty"])):
                    with mysqlcon.cursor() as cursor:
                        sql = "INSERT INTO `api_booking_confirmation_lines` \
                            (`fk_booking_id`, `fk_booking_line_id`, `api_item_id`, \
                             `service_provider`, `label_code`, `client_item_reference`, \
                             `z_createdTimeStamp`, `z_modifiedTimeStamp`, `fp_scan_data`, \
                             `tally` ) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(
                            sql,
                            (
                                booking["pk_booking_id"],
                                booking_line["pk_lines_id"],
                                f"COPDME{str(booking['b_bookingID_Visual'])}{make_3digit(index)}",
                                booking["vx_freight_provider"],
                                f"COPDME{str(booking['b_bookingID_Visual'])}{make_3digit(index)}",
                                booking_line["client_item_reference"],
                                datetime.datetime.now(),
                                datetime.datetime.now(),
                                "",
                                0,
                            ),
                        )
                        mysqlcon.commit()
                        index += 1


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

    try:
        do_process(mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
