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

# LOCAL
# EMAIL_USERNAME = "dev.deliverme@gmail.com"
# EMAIL_PASSWORD = "Dme1234****"
# EMAIL_SERVER_NAME = "imap.gmail.com"

# DEV & PROD
EMAIL_USERNAME = "data.deliver-me@outlook.com"
EMAIL_PASSWORD = "Dme1234*"
EMAIL_SERVER_NAME = "outlook.office365.com"


def read_email_from_gmail(account, password):
    mail = imaplib.IMAP4_SSL(EMAIL_SERVER_NAME)
    mail.login(account, password)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    mail_ids = data[0]

    id_list = mail_ids.split()

    if len(id_list) > 21:
        first_email_id = int(id_list[-21])
    else:
        first_email_id = 0

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
    update bok_1/bok_2s success and map it to dme_bookings
    """
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pk_auto_id`, `pk_header_id`, `success` \
                FROM `bok_1_headers` \
                WHERE `fk_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        bok_1s = cursor.fetchall()

        if len(bok_1s) == 0:  # Does not exist
            print(f"@401 - No Order found. Order Number: {order_number}")
            # TODO - send back error email to JasonL
            return

        bok_1 = bok_1s[0]
        if not int(bok_1["success"]) in [1, 4]:  # Already mapped
            print(
                f"@402 - Can`t update Booking status({bok_1['success']}). Order Number: {order_number}"
            )
            return

        print(f"@403 - Updating... {order_number}")
        sql = "UPDATE `bok_2_lines` \
            SET `success`=%s \
            WHERE `fk_header_id`=%s"
        cursor.execute(sql, (4, bok_1["pk_header_id"]))

        sql = "UPDATE `bok_1_headers` \
            SET `success`=%s \
            WHERE `pk_auto_id`=%s"
        cursor.execute(sql, (4, bok_1["pk_auto_id"]))

        mysqlcon.commit()

        # Run map sh
        os.popen("sh /opt/chrons/MoveSuccess2ToBookings.sh")


def do_process(mysqlcon):
    """
    - read emails received in last 10 mins
    - check email subject - "JasonL | order number | picking slip printed"
    - map booking from `bok` to `dme_bookings`
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

            # Prevent '135000-' case
            if len(order_number.split("-")) > 1 and order_number.split("-")[1] == "":
                order_number = order_number.split("-")[0]

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
