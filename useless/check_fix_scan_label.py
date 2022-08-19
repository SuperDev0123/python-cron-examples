# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_booking_id`, `e_qty_scanned_fp_total` \
                From `dme_bookings` \
                WHERE `vx_freight_provider`=%s"
        cursor.execute(sql, ("Cope"))
        bookings = cursor.fetchall()

        return bookings


def update_booking(pk_booking_id, e_qty_scanned_fp_total, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
                SET `e_qty_scanned_fp_total`=%s, `z_ModifiedTimeStamp`=%s \
                WHERE `pk_booking_id`=%s"
        cursor.execute(
            sql, (e_qty_scanned_fp_total, datetime.datetime.now().date(), pk_booking_id)
        )
        mysqlcon.commit()


def get_booking_lines(fk_booking_id, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pk_lines_id`, `e_qty_scanned_fp` \
                From `dme_booking_lines` \
                WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (fk_booking_id))
        booking_lines = cursor.fetchall()

        return booking_lines


def update_booking_line(pk_lines_id, e_qty_scanned_fp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_booking_lines` \
                SET `e_qty_scanned_fp`=%s, `z_modifiedTimeStamp`=%s \
                WHERE `pk_lines_id`=%s"
        cursor.execute(
            sql, (e_qty_scanned_fp, datetime.datetime.now().date(), pk_lines_id)
        )
        mysqlcon.commit()


def get_api_bcl(fk_booking_line_id, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT COUNT(tally) \
                FROM `api_booking_confirmation_lines` \
                WHERE `fk_booking_line_id`=%s and tally > 0"
        cursor.execute(sql, (fk_booking_line_id))
        result = cursor.fetchone()
        return result


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)

    for booking in bookings:
        booking_lines = get_booking_lines(booking["pk_booking_id"], mysqlcon)

        e_qty_scanned_fp_total = 0
        updated_booking_line = False
        for booking_line in booking_lines:
            api_bcls_cnt = get_api_bcl(booking_line["pk_lines_id"], mysqlcon)

            if int(api_bcls_cnt["COUNT(tally)"]) != 0:
                e_qty_scanned_fp_total += int(api_bcls_cnt["COUNT(tally)"])

            if (
                booking_line["e_qty_scanned_fp"] is not None
                and int(api_bcls_cnt["COUNT(tally)"])
                != int(booking_line["e_qty_scanned_fp"])
                and int(api_bcls_cnt["COUNT(tally)"]) != 0
            ):
                updated_booking_line = True
                update_booking_line(
                    booking_line["pk_lines_id"],
                    int(api_bcls_cnt["COUNT(tally)"]),
                    mysqlcon,
                )
                print("@1 - ", booking_line["pk_lines_id"])

        if update_booking_line:
            update_booking(booking["pk_booking_id"], e_qty_scanned_fp_total, mysqlcon)


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

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
