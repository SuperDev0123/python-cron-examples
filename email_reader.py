# Python 3.7.0
# V 1.0

import imaplib
import email
import pytz
import time
import json
from datetime import datetime
import os, sys, json
import pymysql, pymysql.cursors
import requests
import traceback

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option
from _email_lib import send_email
from _time_lib import sydney_to_utc

IS_PRODUCTION = False
if not IS_PRODUCTION:  # LOCAL
    EMAIL_USERNAME = "dev.deliverme@gmail.com"
    EMAIL_PASSWORD = "Dme1234****"
    EMAIL_SERVER_NAME = "imap.gmail.com"
elif IS_PRODUCTION:  # DEV & PROD
    EMAIL_USERNAME = "data.deliver-me@outlook.com"
    EMAIL_PASSWORD = "Dme1234*"
    EMAIL_SERVER_NAME = "outlook.office365.com"


def get_token():
    url = API_URL + "/api-token-auth/"
    data = {"username": "jason.l_bizsystem", "password": "(Pkm7s,9]Z&Fyw9Q"}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def _pull_order(order_number, token, shipping_type, pusher, b_53):
    """
    Pull an Order from JasonL
    """

    url = API_URL + "/boks/"
    data = {
        "booking": {
            "b_client_order_num": order_number,
            "shipping_type": shipping_type,
            "b_client_sales_inv_num": order_number,
            "b_053_b_del_delivery_type": b_53,
            "pusher": pusher,
        },
        "is_from_script": True,
    }
    print("@900 - Data: ", data)
    headers = {"Authorization": f"JWT {token}"}
    response = requests.post(url, params={}, json=data, headers=headers)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    print("@901 - Result: ", data0)
    return data0


def read_email_from_gmail():
    mail = imaplib.IMAP4_SSL(EMAIL_SERVER_NAME)
    mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    mail_ids = data[0]

    id_list = mail_ids.split()

    if len(id_list) > 51:
        first_email_id = int(id_list[-51])
    else:
        first_email_id = 0

    latest_email_id = int(id_list[-1])

    current_time_seconds = time.time()
    res = []

    with mysqlcon.cursor() as cursor:
        sql = "SELECT `arg1` \
                FROM `dme_options` \
                WHERE `option_name`=%s"
        cursor.execute(sql, ("check_received_emails"))
        option = cursor.fetchone()

    for i in range(latest_email_id, first_email_id, -1):
        if i <= option["arg1"]:
            continue

        result, data = mail.fetch(str(i), "(RFC822)")

        b = email.message_from_bytes(data[0][1])
        try:
            if b.is_multipart():
                for part in b.get_payload():
                    content = part.get_payload()
                    if isinstance(content, list):
                        content = content[0].get_payload()
                        content = content.replace("Pronto Xi Event Id: 83", "")
                        content = content.replace("Jason L Office Furniture", "")
                        content = content.replace("\r\n", "")
                    break
            else:
                content = b.get_payload()
        except Exception as e:
            pass

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

            res.append(
                {
                    "subject": email_subject,
                    "received_time": str(received_time_obj),
                    "content": content,
                }
            )

    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_options` SET arg1=%s WHERE option_name=%s"
        cursor.execute(sql, (latest_email_id, "check_received_emails"))
        mysqlcon.commit()

    return res


def update_booking(mysqlcon, order_number, shipping_type, address_type, pusher, token):
    """
    update bok_1/bok_2s success and map it to dme_bookings
    """

    has_no_address_type = False
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pk_auto_id`, `pk_header_id`, `success`, `b_092_booking_type`, `b_053_b_del_address_type` \
                FROM `bok_1_headers` \
                WHERE `fk_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        bok_1 = cursor.fetchone()

        if bok_1:
            if int(bok_1["success"]) in [1, 4]:  # Already mapped
                print(
                    f"@404 - Already mapped! Order Number: {order_number}, success Code: {bok_1['success']}"
                )
                return False

            shipping_type = bok_1["b_092_booking_type"]
            b_53 = bok_1["b_053_b_del_address_type"]
        else:
            shipping_type = shipping_type
            b_53 = None

            if address_type and address_type[0].upper() == "B":
                b_53 = "Business"
            elif address_type and address_type[0].upper() == "R":
                b_53 = "Residential"

        if not shipping_type or not b_53:
            has_no_address_type = True

            if not shipping_type:
                shipping_type = "DMEA"

            if not b_53:
                b_53 = "Business"

        # Pull Order from JasonL
        _pull_order(order_number, token, shipping_type, pusher, b_53)
        print(f"@402 - PULLED! Order Number: {order_number}")
        time.sleep(60)

    with mysqlcon.cursor() as cursor:
        mysqlcon.commit()
        sql = "SELECT `pk_auto_id`, `pk_header_id`, `success` \
                FROM `bok_1_headers` \
                WHERE `fk_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        bok_1 = cursor.fetchone()
        print(f"@403 - ", bok_1)

        if not bok_1:
            print(f"@400 - Order doens't exist! Order Number: {order_number}")
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

        # # Wait while unlocked
        # mapping_script_flag = False
        # while not mapping_script_flag:
        #     option = get_option(mysqlcon, "MoveSuccess2ToBookings")
        #     mapping_script_flag = option["is_running"]

        #     if mapping_script_flag:
        #         print(f"@410 - MoveSuccess2ToBookings is running, waiting 30s...")
        #         time.sleep(30)

        # # Run map sh
        # print(f"@411 - start mapping...")
        # os.popen("sh /opt/chrons/MoveSuccess2ToBookings.sh")
        # print(f"@412 - finish mapping...")

        if has_no_address_type:
            time.sleep(5)
            mysqlcon.commit()

            sql = "SELECT `b_bookingID_Visual` \
                FROM `dme_bookings` \
                WHERE `kf_client_id`=%s AND `b_client_order_num`=%s"
            cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
            booking = cursor.fetchone()
            print(f"@404 - ", booking)
            send_email_no_address_type(order_number, booking["b_bookingID_Visual"])

        return True


def _check_quote(order_number, mysqlcon):
    """
    check quotes and send email when doesn't exist
    """
    time.sleep(5)
    booking = None

    with mysqlcon.cursor() as cursor:
        mysqlcon.commit()
        sql = "SELECT `id`, `pk_booking_id`, `de_email`, `b_client_name`, `b_bookingID_Visual` \
                FROM `dme_bookings` \
                WHERE `kf_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        booking = cursor.fetchone()

    if booking:
        with mysqlcon.cursor() as cursor:
            sql = "SELECT `id` \
                    FROM `api_booking_quotes` \
                    WHERE `fk_booking_id`=%s AND `is_used`=%s"
            cursor.execute(sql, (booking["pk_booking_id"], 0))
            quotes = cursor.fetchall()

    #         if len(quotes) == 0:
    #             text = f"Dear {booking['b_client_name']}\n\
    # Sales Order {order_number} has been received by the warehouse to ship with either address and / or item line errors OR no freight provider selected. \
    # This will prevent freight being booked. Please go Deliver-ME booking {booking['b_bookingID_Visual']} and review the address and line information. \
    # When complete click 'Update' and then 'Price & Time Calc (FC)'. Select the appropriate provider. \
    # Your booking will then be ready for the warehouse to process."
    #             send_email(
    #                 ["customerservice@jasonl.com.au"],
    #                 ["goldj@deliver-me.com.au", "dev.deliverme@gmail.com"],
    #                 [],
    #                 f"No Quotes",
    #                 text,
    #             )
    #             print("@405 - 'No Quotes' email is sent!")
    #         else:
    #             print("@406 - Quotes are available. ")
    else:
        print(f"@403 - Booking doesn't exist! Order Number: {order_number}")


def send_email_no_address_type(order_number, b_bookingID_Visual):
    text = f"The address type for Sales Order ({order_number}), Deliver-ME Booking ({b_bookingID_Visual}) was not set to Business or Residential in Pronto prior to the booking being sent to Deliver-ME. \
Your booking has thus been created in Deliver-ME with the delivery address defaulted to type - Business. \
Freight pricing will be calculated for this address type. If you need to change it you can do so in Deliver-ME. \
If you update this setting, don't forget to click the 'Update' button to save your changes and then click the 'Price & Time Calc (FC)' button to select your freight option for this change."
    send_email(
        ["customerservice@jasonl.com.au"],
        ["goldj@deliver-me.com.au", "dev.deliverme@gmail.com"],
        [],
        f"No Delivery Address Type OR No Shipping Type",
        text,
    )
    print("@410 - 'No Address Type' email is sent!")


def _send_email_to_admin(subject, text):
    send_email(
        ["goldj@deliver-me.com.au", "daniely@deliver-me.com.au"],
        ["dev.deliverme@gmail.com"],
        [],
        subject,
        text,
    )


def is_order_num(order_num):
    index = 0
    for m in order_num:
        if not (m.isdigit() or m.isspace()):
            break
        index = index + 1
    return True if index > 3 else False


def _extract_info(email_text):
    """
    Extract info from `Bast Assembly` tracking email

    i.e:
        * "Just to confirm your job: 1042079 23855 1042180 23856, has now been received in our warehouse. The date and time of the receive is: 09/05/2022 Free storage time finish at 23/05/2022"
        * "Just to confirm your job: 20235 James Dugand Williams Corporation Level 6, 10 Queen street Melbourne VIC 3000 has now been Scheduled. The date and time of the job is: 7:00 11/05/2022"
        * "Just to confirm your job: 20185 Tennis Victoria110/102 Olympic Boulevard Melbourne VIC 3000 has now been Rescheduled. The date and time of the job is: 8:00 16/05/2022 "
        * "Just to confirm your job: 20144 Alistair Reid 36 Augusta Street Glen Huntly VIC 3163 has now been Completed. The date and time of the job is: 10/05/2022"
    """
    email_text = "".join(email_text.splitlines())
    email_text = email_text.replace("=", "").lower()
    email_text = email_text.replace("please do not", " please do not ").lower()
    print("\n@101 - ", email_text)

    pre_order_str = "just to confirm your job: "
    pre_date_str = "the date and time"
    order_index = email_text.find(pre_order_str)
    date_index = email_text.find(pre_date_str)

    order_extract_str = email_text[order_index + len(pre_order_str) :]
    order_extract_arr = order_extract_str.replace(",", "").strip().split(" ")
    order_nums = []
    for order_num in order_extract_arr:
        if is_order_num(order_num):
            order_nums.append(order_num)
        else:
            break

    # new_result = re.findall('[0-9]+', order_extract_str)
    date_extract_str = email_text[date_index + len(pre_date_str) :]
    index = 0
    for m in date_extract_str:
        if m.isdigit():
            break
        index = index + 1

    date_result = date_extract_str[index:]
    date_part = ""
    for m in date_result:
        if not (m.isdigit() or m.isspace() or m in ["/", ":"]):
            break
        date_part = date_part + m

    if len(date_part.strip().split(" ")) > 1:
        event_at = datetime.strptime(date_part.strip()[:16], "%H:%M %d/%m/%Y")
    else:
        event_at = datetime.strptime(date_part.strip()[:10], "%d/%m/%Y")

    event_at = sydney_to_utc(event_at)

    # Scan Data
    scan_info = None
    if "been received in our warehouse" in email_text:
        scan_info = "RECEIVED BY MEL DEPOT"
    elif "been scheduled" in email_text:
        scan_info = "DELIVERY SCHEDULED"
    elif "been rescheduled" in email_text:
        scan_info = "DELIVERY RESCHEDULED"
    elif "been completed" in email_text:
        scan_info = "DELIVERED TO CUSTOMER"

    print("\nOrderNum: ", order_nums, "Event At: ", event_at, "Scan Info: ", scan_info)

    return order_nums, event_at, scan_info


# TEST _extract_info
# _extract_info(
#     "Just to confirm your job: 1042079 23855 1042180 23856, has now been received in our warehouse. The date and time of the receive is: 09/05/2022 Free storage time finish at 23/05/2022"
# )
# _extract_info(
#     "Just to confirm your job: 10005 has now been received in our warehouse. The date and time of the receive is: 09/05/2022 Free storage time finish at 23/05/2022"
# )
# _extract_info(
#     "Just to confirm your job: 20235 James Dugand Williams Corporation Level 6, 10 Queen street Melbourne VIC 3000 has now been Scheduled. The date and time of the job is: 7:00 11/05/2022"
# )
# _extract_info(
#     "Just to confirm your job: 20185 Tennis Victoria110/102 Olympic Boulevard Melbourne VIC 3000 has now been Rescheduled. The date and time of the job is: 8:00 16/05/2022 "
# )
# _extract_info(
#     "Just to confirm your job: 20144 Alistair Reid 36 Augusta Street Glen Huntly VIC 3163 has now been Completed. The date and time of the job is: 10/05/2022"
# )


def _get_order(order_number, mysqlcon):
    """
    Get JasonL order with order_number
    """

    with mysqlcon.cursor() as cursor:
        mysqlcon.commit()
        sql = "SELECT `id`, `pk_booking_id`, `b_bookingID_Visual` \
                FROM `dme_bookings` \
                WHERE `kf_client_id`=%s AND `b_client_order_num`=%s"
        cursor.execute(sql, ("1af6bcd2-6148-11eb-ae93-0242ac130002", order_number))
        booking = cursor.fetchone()

    return booking


def do_process(mysqlcon):
    """
    - read emails received in last 10 mins
    - check email subject - "JasonL | order number | picking slip printed"
    - map booking from `bok` to `dme_bookings`

    REFACTOR:
    - check email content - "JasonL | (order)-(suffix) | (shipping type) | (address type) | picking slip printed"
    """

    print("@800 - Reading 50 recent emails...")
    emails = read_email_from_gmail()

    if emails:
        token = get_token()

    for email in emails:
        subject = email["subject"]
        content = email["content"]
        content_items = content.split("|")

        # JasonL `Picking Slip Print` email
        if (
            content_items[0].strip().lower() == "jasonl"
            and "picking slip printed" in content_items[4].strip().lower()
        ):
            if len(content_items) != 5:
                continue

            order_number = content_items[1].strip()
            shipping_type = content_items[2].strip()
            address_type = content_items[3].strip()
            pusher = ""

            # Prevent '135000-' case
            if len(order_number.split("-")) > 1 and order_number.split("-")[1] == "":
                order_number = order_number.split("-")[0]

            print(f"@801 - {content}")
            is_updated = update_booking(
                mysqlcon, order_number, shipping_type, address_type, pusher, token
            )

            print(
                f"\n@802 - order_number: {order_number}, {'MAPPED!' if is_updated else 'NOT MAPPED'}"
            )

            if is_updated:
                _check_quote(order_number, mysqlcon)
        # Best Assembly `tracking` email
        elif "job status update" in subject:
            try:
                order_nums, event_at, scan_info = _extract_info(content)
            except Exception as e:
                _send_email_to_admin(
                    "Email Reader: Best Assembly tracking",
                    f"Dear Developer,\n\nFailed to extract info from email.\n\n\nEmail content: {content}\n\nBest,\nDME Cron",
                )
                print(f"@403 - Failed to extract info from email. Error: {str(e)}")
                traceback.print_exc()

            for order_number in order_nums:
                order = _get_order(order_number, mysqlcon)

                if order:
                    cursor = mysqlcon.cursor()
                    if scan_info in ["RECEIVED BY MEL DEPOT"]:
                        sql = "UPDATE `dme_bookings` \
                            SET `s_06_Latest_Delivery_Date_TimeSet`=%s \
                            WHERE `id`=%s"
                        cursor.execute(sql, (event_at, order["id"]))
                        sql = "INSERT INTO `fp_status_history` \
                            (`booking_id`, `fp_id`, `status`, `desc`, `event_timestamp`, `is_active`) \
                            VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(
                            sql, (order["id"], 100, scan_info, content, event_at, 1)
                        )
                        mysqlcon.commit()
                    elif scan_info in ["DELIVERY SCHEDULED"]:
                        sql = "UPDATE `dme_bookings` \
                            SET `s_06_Latest_Delivery_Date_TimeSet`=%s \
                            WHERE `id`=%s"
                        cursor.execute(sql, (event_at, order["id"]))
                        sql = "INSERT INTO `fp_status_history` \
                            (`booking_id`, `fp_id`, `status`, `desc`, `event_timestamp`, `is_active`) \
                            VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(
                            sql, (order["id"], 100, scan_info, content, event_at, 1)
                        )
                        mysqlcon.commit()
                    elif scan_info in ["DELIVERY RESCHEDULED"]:
                        sql = "UPDATE `dme_bookings` \
                            SET `s_06_Latest_Delivery_Date_Time_Override`=%s \
                            WHERE `id`=%s"
                        cursor.execute(sql, (event_at, order["id"]))
                        sql = "INSERT INTO `fp_status_history` \
                            (`booking_id`, `fp_id`, `status`, `desc`, `event_timestamp`, `is_active`) \
                            VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(
                            sql, (order["id"], 100, scan_info, content, event_at, 1)
                        )
                        mysqlcon.commit()
                    elif scan_info in ["DELIVERED TO CUSTOMER"]:
                        sql = "UPDATE `dme_bookings` \
                            SET `s_21_Actual_Delivery_TimeStamp`=%s, `b_status`=%s, `b_status_category`=%s, `z_lock_status`=%s \
                            WHERE `id`=%s"
                        cursor.execute(
                            sql, (event_at, "Delivered", "Completed", 1, order["id"])
                        )
                        sql = "INSERT INTO `fp_status_history` \
                            (`booking_id`, `fp_id`, `status`, `desc`, `event_timestamp`, `is_active`) \
                            VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(
                            sql, (order["id"], 100, scan_info, content, event_at, 1)
                        )
                        mysqlcon.commit()
                    else:
                        _send_email_to_admin(
                            "Email Reader: Best Assembly tracking",
                            f"Dear Developer,\n\nUnknown Scan info: {scan_info}\n\nEmail content: {content}\n\nBest,\nDME Cron",
                        )
                        print(f"@401 - Unknown Scan info: {scan_info}")
                else:
                    _send_email_to_admin(
                        "Email Reader: Best Assembly tracking",
                        f"Dear Developer,\n\nJasonL order does not exist - {order_number}\n\n\nEmail content: {content}\n\nBest,\nDME Cron",
                    )
                    print(f"@402 - JasonL order does not exist - {order_number}")


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
    except Exception as e:
        print("#904 Error:", str(e))
        set_option(mysqlcon, "check_received_emails", False, time1)

    mysqlcon.close()
    print("#909 - Finished %s\n\n\n" % datetime.now())
