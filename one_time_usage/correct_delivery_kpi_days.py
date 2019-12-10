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
    DB_NAME = "dme_db_dev"  # Dev
    # DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `de_To_Address_PostalCode` \
                From `dme_bookings` \
                WHERE `vx_freight_provider`=%s"
        cursor.execute(sql, ("Cope"))
        bookings = cursor.fetchall()
        print("Cope bookings cnt: ", len(bookings))
        return bookings


def fix_delivery_kpi_days(bookings, mysqlcon):
    with mysqlcon.cursor() as cursor:
        for index, booking in enumerate(bookings):
            if index % 500 == 0:
                print("@200 - ", index, booking["de_To_Address_PostalCode"])

            sql = "SELECT * \
                    FROM `utl_fp_delivery_times` \
                    WHERE `postal_code_from`<=%s and `postal_code_to`>=%s"
            cursor.execute(
                sql,
                (
                    int(booking["de_To_Address_PostalCode"]),
                    int(booking["de_To_Address_PostalCode"]),
                ),
            )
            result = cursor.fetchone()

            if result:
                sql = "UPDATE `dme_bookings` \
                   SET delivery_kpi_days = %s \
                   WHERE id=%s"
                cursor.execute(sql, (result["delivery_days"], booking["id"]))
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

    bookings = get_bookings(mysqlcon)
    fix_delivery_kpi_days(bookings, mysqlcon)

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
