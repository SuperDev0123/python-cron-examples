# Python 3.7.0
# V 1.0

import imaplib
import email
import time
from datetime import datetime
import os, sys, json
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


EMAIL_USERNAME = "dev.deliverme@gmail.com"
EMAIL_PASSWORD = "Dme1234****"


def read_email_from_gmail(account, password):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(account, password)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    mail_ids = data[0]

    id_list = mail_ids.split()
    first_email_id = int(id_list[-21])
    latest_email_id = int(id_list[-1])  # Check 20 recent emails

    current_time_seconds = time.time()
    res = []

    for i in range(latest_email_id, first_email_id, -1):
        result, data = mail.fetch(str(i), "(RFC822)")

        for response_part in data:
            if not isinstance(response_part, tuple):
                continue

            msg = email.message_from_bytes(response_part[1])
            email_subject = msg["subject"]
            email_from = msg["from"]
            email_received_time = msg["Date"]

            if len(email_received_time) == 29:
                email_received_time = email_received_time[:25] + " +0000"  # GMT
            else:
                email_received_time = email_received_time[:31]  # NON-GMT

            received_time_obj = datetime.strptime(
                email_received_time.strip(), "%a, %d %b %Y %H:%M:%S %z"
            )

            time_diff = current_time_seconds - received_time_obj.timestamp()

            if time_diff <= 60 * 10:  # Check if received in last 10 mins
                res.append(
                    {"subject": email_subject, "received_time": str(received_time_obj)}
                )

    return res


def update_booking(order_number, mysqlcon):
    """
    update booking status if only `b_status` is `Picking`
    """
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_status` \
                FROM `dme_bookings` \
                WHERE `b_client_name`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("Jason L", order_number))
        bookings = cursor.fetchall()

        if len(bookings) == 0:
            print(f"@401 - No booking found. Order Number: {order_number}")
            # TODO - send back error email to JasonL
            return

        booking = bookings[0]
        if not booking["b_status"] in ["Picking", "Pre Booking"]:
            print(
                f"@402 - Can`t update Booking status({booking['b_status']}). Order Number: {order_number}"
            )
            # TODO - send back error email to JasonL
            return

        sql = "UPDATE `dme_bookings` \
            SET `b_status`=%s, b_dateBookedDate=%s \
            WHERE `id`=%s"
        cursor.execute(sql, ("Ready for Despatch", datetime.now(), booking["id"]))
        mysqlcon.commit()


def do_process(mysqlcon):
    """
    - read emails received in last 10 mins
    - check email subject - "JasonL | order number | picking slip printed"
    - set the `b_status` as `Ready for Despatch`
    """

    print("@800 - Reading 50 recent emails...")
    emails = read_email_from_gmail(EMAIL_USERNAME, EMAIL_PASSWORD)

    for email in emails:
        subject = email["subject"]
        subject_items = subject.split("|")

        if len(subject_items) != 3:
            continue

        if (
            subject_items[0].strip().lower() == "jasonl"
            and subject_items[2].strip().lower() == "picking slip printed"
        ):
            order_number = subject_items[1].strip().lower()
            print(f"\n@801 - order_number: {order_number}")
            update_booking(order_number, mysqlcon)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.now())
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
        option = get_option(mysqlcon, "check_received_emails")

        if int(option["option_value"]) == 0:
            print("#905 - `check_received_emails` option is OFF")
        elif option["is_running"]:
            print("#905 - `check_received_emails` script is already RUNNING")
        else:
            print("#906 - `check_received_emails` option is ON")
            set_option(mysqlcon, "check_received_emails", True)
            do_process(mysqlcon)
            set_option(mysqlcon, "check_received_emails", False, time1)
    except OSError as e:
        print("#904 Error:", str(e))
        set_option(mysqlcon, "check_received_emails", False, time1)

    mysqlcon.close()
    print("#909 - Finished %s" % datetime.now())
