# Python 3.7.0
# V 1.0

import imaplib
import email
import time
from datetime import datetime
import os, sys, json
import pymysql, pymysql.cursors
import requests

from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    API_URL,
    USERNAME,
    PASSWORD,
)
from _options_lib import get_option, set_option
from _email_lib import send_email

# LOCAL
# EMAIL_USERNAME = "dev.deliverme@gmail.com"
# EMAIL_PASSWORD = "Dme1234****"
# EMAIL_SERVER_NAME = "imap.gmail.com"

# DEV & PROD
EMAIL_USERNAME = "data.deliver-me@outlook.com"
EMAIL_PASSWORD = "Dme1234*"
EMAIL_SERVER_NAME = "outlook.office365.com"


def get_token():
    url = API_URL + "/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def _pull_order(order_number):
    """
    Pull an Order from JasonL
    """
    token = get_token()

    url = API_URL + "/api/boks/"
    data = {
        "booking": {
            "b_client_order_num": order_number,
            "shipping_type": "DMEA",
            "b_client_sales_inv_num": {order_number},
            "b_053_b_del_delivery_type": "business",
        }
    }
    headers = {"Authorization": f"JWT {token}"}
    response = requests.post(url, params={}, json=data, headers=headers)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    print("@901 - Result: ", data0)
    return data0


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

            # Pull Order from JasonL
            _pull_order(order_number)

            sql = "SELECT `pk_auto_id`, `pk_header_id`, `success` \
                    FROM `bok_1_headers` \
                    WHERE `fk_client_id`=%s AND `b_client_order_num`=%s"
            cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
            bok_1s = cursor.fetchall()

        bok_1 = bok_1s[0]
        if int(bok_1["success"]) in [1, 4]:  # Already mapped
            print(
                f"@402 - Already mapped! Order Number: {order_number}, success Code: {bok_1['success']}"
            )
            return False

        print(f"@403 - Updating... {order_number}")
        sql = "UPDATE `bok_2_lines` \
            SET `success`=%s \
            WHERE `fk_header_id`=%s"
        cursor.execute(sql, (4, bok_1["pk_header_id"]))

        sql = "UPDATE `bok_3_lines_data` \
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

        return True


def _check_quote(order_number, mysqlcon):
    """
    check quotes and send email when doesn't exist
    """
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_header_id`, `de_email`, `b_client_name`, `b_booking_visualID` \
                FROM `dme_bookings` \
                WHERE `fk_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        booking = cursor.fetchone()

        if booking:
            sql = "SELECT `id` \
                    FROM `api_booking_quotes` \
                    WHERE `fk_client_id`=%s AND `is_used`=%s"
            cursor.execute(sql, (booking["fk_booking_id"], 0))
            quotes = cursor.fetchall()

            if len(quotes) > 0:
                text = f"Dear {booking['b_client_name']}\n\
                    Sales Order {order_number} has been received by the warehouse to ship with either address and / or item line errors OR no freight provider selected. \
                    This will prevent freight being booked. Please go Deliver-ME booking {booking['b_bookingID_Visual']} and review the address and line information. \
                    When complete click 'Update' and then 'Price & Time Calc (FC)'. Select the appropriate provider. \
                    Your booking will then be ready for the warehouse to process."
                send_email(
                    ["customerservice@jasonl.com.au"],
                    [
                        "stephenm@deliver-me.com.au",
                        "petew@deliver-me.com.au",
                        "goldj@deliver-me.com.au",
                    ],
                    f"No Quotes",
                    text,
                )
        else:
            print(f"@403 - Booking doesn't exist! Order Number: {order_number}")


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
            is_updated = update_booking(order_number, mysqlcon)

            print(
                f"\n@802 - order_number: {order_number}, {'MAPPED!' if is_updated else 'NOT MAPPED'}"
            )
            _check_quote(order_number, mysqlcon)


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
