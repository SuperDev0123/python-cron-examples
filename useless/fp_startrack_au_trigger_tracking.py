# Python 3.6.6

import sys, time, os
import datetime
from datetime import timedelta
import uuid
import urllib, requests, json
import pymysql, pymysql.cursors
import base64, pytz

import _status_history

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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

BIOPAK_AUTH_TOKEN = "edZIsxP0vEnC3jcNYfPvIg=="

# DME_LEVEL_API_URL = "http://localhost:3000"  # Local
# DME_LEVEL_API_URL = "http://52.62.109.115:3000" # Dev
DME_LEVEL_API_URL = "http://52.62.102.72:3000"  # Prod

FK_CLIENT_WAREHOUSE_IDS_AND_ACCOUNT_NUMBERS = [
    {"warehouse_id": 16, "account_number": "10149943", "warehouse_name": "EasternC"},
    {
        "warehouse_id": 7,
        "account_number": "10145597",
        "warehouse_name": "Hazelmere (WA)",
    },
    {
        "warehouse_id": 6,
        "account_number": "10149944",
        "warehouse_name": "Truganina (VIC)",
    },
    {"warehouse_id": 5, "account_number": "10145596", "warehouse_name": "Cavan (SA)"},
    {
        "warehouse_id": 4,
        "account_number": "10145593",
        "warehouse_name": "Rocklea (QLD)",
    },
    {
        "warehouse_id": 3,
        "account_number": "10145902",
        "warehouse_name": "Bondi Junction",
    },
]


def get_sydney_now_time(return_type="char"):
    sydney_tz = pytz.timezone("Australia/Sydney")
    sydney_now = sydney_tz.localize(datetime.datetime.utcnow())
    sydney_now = sydney_now + timedelta(hours=10)

    if return_type == "char":
        return sydney_now.strftime("%Y-%m-%d %H:%M:%S")
    elif return_type == "datetime":
        return sydney_now


def _update_booking_with_error(consignmentNumber, error_message, mysqlcon):
    # with mysqlcon.cursor() as cursor:
    #     cursor.execute(
    #         "UPDATE `dme_bookings` \
    #         SET `b_error_Capture` = %s \
    #         WHERE `v_FPBookingNumber` = %s",
    #         (error_message, consignmentNumber),
    #     )
    #     mysqlcon.commit()
    print("@402 - Set b_error_Capture: ", consignmentNumber, error_message)


def get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `kf_FP_ID`, `b_bookingID_Visual`, `pk_booking_id`, `b_status_API`, `v_FPBookingNumber`, `b_clientReference_RA_Numbers` \
                FROM `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (v_FPBookingNumber))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result


def _update_booking_and_BIOPAK(trackDetail, mysqlcon, payload, url, booking):
    with mysqlcon.cursor() as cursor:
        try:
            # Save log
            request_payload = {
                "apiUrl": url,
                "accountCode": payload["spAccountDetails"]["accountCode"],
                "authKey": payload["spAccountDetails"]["accountKey"],
                "trackingId": payload["consignmentDetails"][0]["consignmentNumber"],
            }
            request_type = "TRACKING"
            request_status = "SUCCESS"

            temp = ""
            if booking["kf_FP_ID"]:
                temp = booking["kf_FP_ID"]
            sql = "INSERT INTO `dme_log` \
                (`request_payload`, `request_status`, `request_type`, `response`, `fk_booking_id`,`fk_service_provider_id`) \
                VALUES (%s, %s, %s, %s, %s,%s)"
            cursor.execute(
                sql, ("", request_status, request_type, response0, booking["id"], temp)
            )
            mysqlcon.commit()

            # Update booking and BIOPAK
            try:
                new_status = trackDetail["consignmentStatuses"][0]["status"]
                try:
                    event_time_stamp = trackDetail["consignmentStops"][0]["transitDate"]
                except IndexError:
                    event_time_stamp = None

                if booking["b_status_API"] != new_status:
                    print(
                        "@601 - ",
                        "Old Status:",
                        booking["b_status_API"],
                        "New Status:",
                        new_status,
                    )
                else:
                    print("@601 - SAME STATUS:", new_status)

                if booking["b_status_API"] != new_status:
                    # Create dme_status_history
                    _status_history.create(booking["id"], new_status, event_time_stamp)

                    # Fetch option flag
                    sql = "SELECT `option_value` \
                        FROM dme_options \
                        WHERE option_name = %s"
                    cursor.execute(sql, ("status_update_for_biopak"))
                    result = cursor.fetchone()

                    # Update BIOPAK
                    if result["option_value"] == "1":
                        try:
                            params = {
                                "consignment_number": booking["v_FPBookingNumber"],
                                "b_status_API": new_status,
                                "event_date": event_time_stamp,
                                "b_clientReference_RA_Numbers": booking[
                                    "b_clientReference_RA_Numbers"
                                ],
                            }
                            headers = {
                                "content-type": "application/json",
                                "API-TOKEN": BIOPAK_AUTH_TOKEN,
                            }
                            print("@602 - ", "Update BIOPAK: ", params)
                            response1 = requests.get(
                                "https://www.workato.com/webhooks/rest/22e2379b-377a-48f1-9ccd-8dc38a5d0289/receive_tracking_updates",
                                headers=headers,
                                params=params,
                            )
                        except requests.exceptions.ConnectionError:
                            print("@405 - WORKATO(BIOPAK api) connection problem")

                # Update dme_bookings
                sql = "UPDATE `dme_bookings` \
                    SET b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                    WHERE v_FPBookingNumber=%s"
                cursor.execute(
                    sql,
                    (new_status, datetime.datetime.now(), booking["v_FPBookingNumber"]),
                )
                mysqlcon.commit()

                print("@200 - SUCCESS: ", booking["b_bookingID_Visual"])
            except IndexError as e:
                print("@500 - error : ", booking["id"], e)

            # Disable tracking if `delivered in full`
            if (
                booking["b_status_API"]
                and booking["b_status_API"].lower() == "delivered in full"
            ) or new_status.lower() == "delivered in full":
                sql = "UPDATE `dme_bookings` \
                    SET b_status_API=%s, z_api_issue_update_flag_500=%s \
                    WHERE v_FPBookingNumber=%s"
                cursor.execute(
                    sql, ("Delivered in Full", "0", booking["v_FPBookingNumber"])
                )
                mysqlcon.commit()
        except KeyError as e:
            print("@609 - error : ", e)


def do_process(data, mysqlcon, bookings, index, payload, url):
    if not data:
        # for i in range(index * 10, (index + 1) * 10):
        #     _update_booking_with_error(
        #         bookings[i]["v_FPBookingNumber"], "INVALID_TRACKING_ID", mysqlcon
        #     )
        return
    try:
        if data[0]["error_code"] == "API_002":  # Too many requests
            print("@300 - Sleep: 1 minutes (%s)" % datetime.datetime.now())
            time.sleep(60)
            return
    except KeyError:
        try:
            for index, trackDetail in enumerate(data["consignmentTrackDetails"]):
                try:
                    if trackDetail["code"] == "ESB-10001":  # Invalid tracking ID
                        _update_booking_with_error(
                            trackDetail["consignmentNumber"],
                            trackDetail["message"],
                            mysqlcon,
                        )
                    else:
                        print("@301 - ", trackDetail)
                except KeyError:
                    booking = get_booking_with_v_FPBookingNumber(
                        trackDetail["consignmentNumber"], mysqlcon
                    )
                    print(
                        "@302 - ",
                        booking["b_bookingID_Visual"],
                        ":",
                        trackDetail["consignmentNumber"],
                    )
                    _update_booking_and_BIOPAK(
                        trackDetail, mysqlcon, payload, url, booking
                    )
        except TypeError:
            print("@401 - ", data)
        except KeyError:
            print("@402 - ", data)


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

    for wian in FK_CLIENT_WAREHOUSE_IDS_AND_ACCOUNT_NUMBERS:
        with mysqlcon.cursor() as cursor:
            sql = "SELECT `id`, `b_bookingID_Visual`, `v_FPBookingNumber`, `b_status_API`, `kf_FP_ID` \
                FROM `dme_bookings` \
                WHERE LOWER(`vx_freight_provider`)=%s AND `b_status`=%s AND `z_api_issue_update_flag_500`=%s \
                        AND (`b_error_Capture` IS NULL OR `b_error_Capture` = %s) \
                        AND `fk_client_warehouse_id` = %s \
                ORDER BY id DESC"
            cursor.execute(sql, ("startrack", "Booked", 1, "", wian["warehouse_id"]))
            booking_list = cursor.fetchall()
            print(
                "@100 - Warehouse:",
                wian["warehouse_name"],
                "Bookings cnt: ",
                len(booking_list),
            )

        for index in range(int(len(booking_list) / 10)):  # Batch - 10
            print(
                "@101 - ",
                wian["warehouse_name"],
                ":",
                index * 10,
                "/",
                len(booking_list),
            )
            # for index in range(int(len(booking_list))):  # Single
            #     print(
            #         "@102 - ",
            #         wian["warehouse_name"],
            #         ":",
            #         index,
            #         "/",
            #         len(booking_list),
            #         "-",
            #         booking_list[index]["b_bookingID_Visual"],
            #     )

            consignmentDetails = []
            for i in range(index * 10, (index + 1) * 10):  # Batch - 10
                consignmentDetails.append(
                    {"consignmentNumber": booking_list[i]["v_FPBookingNumber"]}
                )
            # consignmentDetails.append(  # Single
            #     {"consignmentNumber": booking_list[index]["v_FPBookingNumber"]}
            # )

            payload = {}
            payload["consignmentDetails"] = consignmentDetails
            payload["spAccountDetails"] = {
                "accountCode": wian["account_number"],
                "accountPassword": "x81775935aece65541c9",
                "accountKey": "d36fca86-53da-4db8-9a7d-3029975aa134",
            }
            payload["serviceProvider"] = "ST"

            try:
                # print("@101 Payload:", payload)
                url = DME_LEVEL_API_URL + "/tracking/trackconsignment"
                response0 = requests.post(url, params={}, json=payload)
                response0 = response0.content.decode("utf8")
                data0 = json.loads(response0)
                # s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
                # print("@102 Response:", s0)
            except requests.exceptions.ConnectionError:
                print("@407 - ST api connection problem")

            do_process(data0, mysqlcon, booking_list, index, payload, url)

            time.sleep(30)

    print("#999 - Finished %s" % datetime.datetime.now())
