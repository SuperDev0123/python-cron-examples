# Python 3.6.6
# V 1.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_header_id`, `b_client_order_num`, `b_client_sales_inv_num` \
                FROM `bok_1_headers` \
                WHERE `fk_client_id`=%s, z_CreatedTimestamp < now() - interval 10 minute"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002"))
        bookings = cursor.fetchall()

        return bookings


def delete_booking_and_booking_lines(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "DELETE FROM bok_2_lines WHERE fk_header_id=%s"
        cursor.execute(sql, (booking.pk_header_id))

        sql = "DELETE FROM bok_1_headers WHERE id=%s"
        cursor.execute(sql, (booking.id))


def do_process(mysqlcon):
    """
    Clear JasonL bookings created in last 10 minuntes
    """
    bookings = get_bookings(mysqlcon)
    print("#200 - Booking cnt to be cleared: ", len(bookings))

    for booking in bookings:
        print(
            f"#201 - Order Number: {booking.b_client_order_num}, Sales Invoice No: {booking.b_client_sales_inv_num}"
        )

        delete_booking_and_booking_lines(booking, mysqlcon)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())
    time1 = time.time()

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
        option = get_option(mysqlcon, "jasonL_clear")

        if int(option["option_value"]) == 0:
            print("#905 - `jasonL_clear` option is OFF")
        elif option["is_running"]:
            print("#905 - `jasonL_clear` script is already RUNNING")
        else:
            print("#906 - `jasonL_clear` option is ON")
            set_option(mysqlcon, "jasonL_clear", True)
            do_process(mysqlcon)
            set_option(mysqlcon, "jasonL_clear", False, time1)
    except OSError as e:
        print("#904 Error:", str(e))
        set_option(mysqlcon, "jasonL_clear", False, time1)

    mysqlcon.close()
    print("#909 - Finished %s" % datetime.datetime.now())
