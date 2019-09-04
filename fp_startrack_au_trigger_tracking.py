# Python 3.6.6

import sys, time, os
import datetime
from datetime import timedelta
import uuid
import urllib, requests, json
import pymysql, pymysql.cursors
import base64, pytz

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


def get_sydney_now_time(return_type="char"):
    sydney_tz = pytz.timezone("Australia/Sydney")
    sydney_now = sydney_tz.localize(datetime.datetime.utcnow())
    sydney_now = sydney_now + timedelta(hours=10)

    if return_type == "char":
        return sydney_now.strftime("%Y-%m-%d %H:%M:%S")
    elif return_type == "datetime":
        return sydney_now


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

    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_bookings` \
            WHERE LOWER(`vx_freight_provider`)=%s and `b_status`=%s and `z_api_issue_update_flag_500`=%s"
        cursor.execute(sql, ("startrack", "Booked", "1"))
        booking_list = cursor.fetchall()

    print("@1 Bookings cnt - ", len(booking_list))
    results = []

    for index, booking in enumerate(booking_list):

        if index > 0 and index % 10 == 0:
            time.sleep(180)

        print("num : ", booking["pk_booking_id"])
        url = "http://52.62.102.72:8081/dme-api/tracking/trackconsignment"
        data = {}
        data["consignmentDetails"] = [
            {"consignmentNumber": booking["v_FPBookingNumber"]}
        ]
        data["spAccountDetails"] = {
            "accountCode": "10149943",
            "accountState": "NSW",
            "accountPassword": "x81775935aece65541c9",
            "accountKey": "d36fca86-53da-4db8-9a7d-3029975aa134",
        }
        data["serviceProvider"] = "ST"

        response0 = requests.post(url, params={}, json=data)
        response0 = response0.content.decode("utf8")
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual

        if "errorCode" in data0:
            print(s0)

        try:
            request_payload = {
                "apiUrl": "",
                "accountCode": "",
                "authKey": "",
                "trackingId": "",
            }
            request_payload["apiUrl"] = url
            request_payload["accountCode"] = data["spAccountDetails"]["accountCode"]
            request_payload["authKey"] = data["spAccountDetails"]["accountKey"]
            request_payload["trackingId"] = data["consignmentDetails"][0][
                "consignmentNumber"
            ]
            request_type = "TRACKING"
            request_status = "SUCCESS"

            with mysqlcon.cursor() as cursor:
                temp = ""
                if booking["kf_FP_ID"]:
                    temp = booking["kf_FP_ID"]
                sql = "INSERT INTO `dme_log` (`request_payload`, `request_status`, `request_type`, `response`, `fk_booking_id`,`fk_service_provider_id`) VALUES (%s, %s, %s, %s, %s,%s)"
                cursor.execute(
                    sql,
                    ("", request_status, request_type, response0, booking["id"], temp),
                )
                mysqlcon.commit()

            try:
                new_status = data0["consignmentTrackDetails"][0]["consignmentStatuses"][
                    0
                ]["status"]
                event_time_stamp = data0["consignmentTrackDetails"][0][
                    "consignmentStops"
                ][0]["transitDate"]
                print("status is fine.")
                if booking["b_status_API"] != new_status:
                    with mysqlcon.cursor() as cursor:
                        sql = (
                            "INSERT INTO `dme_status_history` (`fk_booking_id`, `status_old`, `notes`, `status_last`,"
                            " `z_createdTimeStamp`,`event_time_stamp`) VALUES (%s, %s, %s, %s, %s, %s)"
                        )
                        cursor.execute(
                            sql,
                            (
                                booking["pk_booking_id"],
                                booking["b_status_API"],
                                str(booking["b_status_API"])
                                + " ---> "
                                + str(new_status),
                                new_status,
                                datetime.datetime.now(),
                                event_time_stamp,
                            ),
                        )
                        mysqlcon.commit()

                        # Fetch option flag
                        sql = "SELECT `option_value` \
                            FROM dme_options \
                            WHERE option_name = %s"
                        cursor.execute(sql, ("status_update_for_biopak"))
                        result = cursor.fetchone()
                        print(result["option_value"])
                        if result["option_value"] == "1":
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
                            print("Update status for BIOPAK: ", params)
                            response1 = requests.get(
                                "https://www.workato.com/webhooks/rest/22e2379b-377a-48f1-9ccd-8dc38a5d0289/receive_tracking_updates",
                                headers=headers,
                                params=params,
                            )

                # total_Cubic_Meter_override = data0['consignmentTrackDetails'][0]['totalVolume']
                # total_1_KG_weight_override = data0['consignmentTrackDetails'][0]['totalWeight']
                # total_lines_qty_override = data0['consignmentTrackDetails'][0]['totalItems']
                with mysqlcon.cursor() as cursor:
                    sql = (
                        "Update `dme_bookings` set b_status_API=%s,z_lastStatusAPI_ProcessedTimeStamp=%s"
                        " where id =%s"
                    )
                    cursor.execute(
                        sql, (new_status, datetime.datetime.now(), booking["id"])
                    )
                    mysqlcon.commit()

                if new_status.lower() == "delivered in full":
                    with mysqlcon.cursor() as cursor:
                        # sql = (
                        #     "Update `dme_bookings` set z_api_issue_update_flag_500=%s,"
                        #     "s_21_Actual_Delivery_TimeStamp=%s where id =%s"
                        # )
                        # cursor.execute(
                        #     sql,
                        #     (
                        #         "0",
                        #         data0["consignmentTrackDetails"][0][
                        #             "scheduledDeliveryDate"
                        #         ],
                        #         booking["id"],
                        #     ),
                        # )
                        sql = "Update `dme_bookings` \
                            SET z_api_issue_update_flag_500=%s \
                            WHERE id =%s"
                        cursor.execute(sql, ("0", booking["id"]))
                        mysqlcon.commit()

                # with mysqlcon.cursor() as cursor:
                #     sql = "SELECT * FROM `dme_client_warehouses` where pk_id_client_warehouses=%s"
                #     cursor.execute(sql, (booking["fk_client_warehouse_id"]))
                #     warehouse = cursor.fetchall()
                # try:
                #     print("now pod.")
                #
                #     pod_file = data0['consignmentTrackDetails'][0]["pods"][0]['podData']
                #     print("pod is fine.")
                #
                #     warehouse_name = ''
                #     if warehouse:
                #         warehouse_name = warehouse[0]['client_warehouse_code']
                #     file_name = "POD_" + \
                #                 str(warehouse_name) + "_" + \
                #                 booking['b_clientReference_RA_Numbers'] + "_" + \
                #                 booking['v_FPBookingNumber'] + "_" + \
                #                 str(booking['b_bookingID_Visual']) + '.png'
                #     file_url = '/var/www/html/dme_api/static/imgs/' + file_name
                #
                #     with open(os.path.expanduser(file_url), 'wb') as fout:
                #         fout.write(
                #             base64.decodestring(pod_file.encode('utf-8')))
                #
                #     with mysqlcon.cursor() as cursor:
                #         sql = "Update `dme_bookings` set z_pod_url=%s where id =%s"
                #         cursor.execute(sql, (file_name, booking['id']))
                #         mysqlcon.commit()
                # except IndexError:
                #     print("POD : ", ' empty')

                ## POD
                # try:
                #     print("now sign.")
                #     pod_file = data0["consignmentTrackDetails"][0][
                #         "consignmentStatuses"
                #     ][0]["signatureImage"]
                #     print("sign is fine.")
                #     warehouse_name = ""
                #     if warehouse:
                #         warehouse_name = warehouse[0]["client_warehouse_code"]
                #     file_name = (
                #         "pod_signed_"
                #         + str(warehouse_name)
                #         + "_"
                #         + booking["b_clientReference_RA_Numbers"]
                #         + "_"
                #         + booking["v_FPBookingNumber"]
                #         + "_"
                #         + str(booking["b_bookingID_Visual"])
                #         + ".png"
                #     )
                #     file_url = "/opt/s3_public/imgs/" + file_name

                #     with open(os.path.expanduser(file_url), "wb") as fout:
                #         fout.write(base64.decodestring(pod_file.encode("utf-8")))

                #     with mysqlcon.cursor() as cursor:
                #         sql = (
                #             "Update `dme_bookings` set z_pod_signed_url=%s where id =%s"
                #         )
                #         cursor.execute(sql, (file_name, booking["id"]))
                #         mysqlcon.commit()
                # except IndexError:
                #     print("sign : ", " empty")

                ## SCAN
                # try:
                #     with mysqlcon.cursor() as cursor:
                #         sql = "Update `dme_bookings` set vx_fp_pu_eta_time=%s, vx_fp_del_eta_time=%s, z_lastStatusAPI_ProcessedTimeStamp=%s where id =%s"
                #         cursor.execute(
                #             sql,
                #             (
                #                 data0["consignmentTrackDetails"][0][
                #                     "scheduledPickupDate"
                #                 ],
                #                 data0["consignmentTrackDetails"][0][
                #                     "scheduledDeliveryDate"
                #                 ],
                #                 data0["consignmentTrackDetails"][0]["scannings"][0][
                #                     "scanDate"
                #                 ],
                #                 booking["id"],
                #             ),
                #         )
                #         mysqlcon.commit()
                # except IndexError:
                #     print("Delivery Date ", " no")

                print("success : ", booking["id"])
            except IndexError as e:
                print("error : ", booking["id"])
                print("error : ", e)
        except KeyError as e:
            print("error : ", e)
