# Python 3.6.6

import sys, time
import os
import io
import errno
import uuid
import json
import base64
import shutil
import datetime
import pymysql, pymysql.cursors

production = True  # Dev
# production = False  # Local

if production:
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


def do_process_01(mysqlcon):
    # If b_status = 'In Transit' && qty scanned < qty booked but not Null or 0
    # Then set Status Detail to 'In transporter's depot (partial)'
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, pk_booking_id, b_status, dme_status_detail \
                FROM dme_bookings \
                WHERE b_status=%s"
        cursor.execute(sql, ("In Transit"))
        bookings = cursor.fetchall()

        for booking in bookings:
            sql = "SELECT e_qty_scanned_fp, e_qty \
                FROM dme_booking_lines \
                WHERE fk_booking_id=%s"
            cursor.execute(sql, (booking["pk_booking_id"]))
            booking_lines = cursor.fetchall()

            total_e_qty = 0
            total_e_qty_scanned_fp = 0
            for booking_line in booking_lines:
                if booking_line["e_qty"] is not None:
                    total_e_qty += booking_line["e_qty"]

                if booking_line["e_qty_scanned_fp"] is not None:
                    total_e_qty_scanned_fp += booking_line["e_qty_scanned_fp"]

            if (
                total_e_qty_scanned_fp < total_e_qty
                and total_e_qty_scanned_fp > 0
                and booking["dme_status_detail"] != "In transporter's depot (partial)"
            ):
                sql = "UPDATE dme_bookings \
                    SET dme_status_detail=%s, z_ModifiedTimestamp=%s \
                    WHERE id=%s"
                cursor.execute(
                    sql,
                    (
                        "In transporter's depot (partial)",
                        datetime.datetime.now(),
                        booking["id"],
                    ),
                )
                mysqlcon.commit()
                print("@905 - id: ", booking["id"])


def do_process_02(mysqlcon):
    # If POD exists and scans are less than the qty booked
    # Then set Status Detail to 'Delivered Partial'
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, pk_booking_id, z_pod_url, z_pod_signed_url, dme_status_detail \
                FROM dme_bookings \
                WHERE (z_pod_url <> '' and z_pod_url is not null) \
                    or (z_pod_signed_url <> '' and z_pod_signed_url is not null)"
        cursor.execute(sql)
        bookings = cursor.fetchall()

        for booking in bookings:
            sql = "SELECT e_qty_scanned_fp, e_qty \
                FROM dme_booking_lines \
                WHERE fk_booking_id=%s"
            cursor.execute(sql, (booking["pk_booking_id"]))
            booking_lines = cursor.fetchall()

            total_e_qty = 0
            total_e_qty_scanned_fp = 0
            for booking_line in booking_lines:
                if booking_line["e_qty"] is not None:
                    total_e_qty += booking_line["e_qty"]

                if booking_line["e_qty_scanned_fp"] is not None:
                    total_e_qty_scanned_fp += booking_line["e_qty_scanned_fp"]

            if (
                total_e_qty_scanned_fp < total_e_qty
                and total_e_qty_scanned_fp > 0
                and booking["dme_status_detail"] != "Delivered Partial"
            ):
                sql = "UPDATE dme_bookings \
                    SET dme_status_detail=%s, z_ModifiedTimestamp=%s \
                    WHERE id=%s"
                cursor.execute(
                    sql, ("Delivered Partial", datetime.datetime.now(), booking["id"])
                )
                mysqlcon.commit()
                print("@906 - id: ", booking["id"])


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
        # If b_status = 'In Transit' && qty scanned < qty booked but not Null or 0
        # Then set Status Detail to 'In transporter's depot (partial)'
        do_process_01(mysqlcon)
    except OSError as e:
        print("#902 Error", str(e))

    try:
        # If POD exists and scans are less than the qty booked
        # Then set Status Detail to 'Delivered Partial'
        do_process_02(mysqlcon)
    except OSError as e:
        print("#903 Error", str(e))

    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
