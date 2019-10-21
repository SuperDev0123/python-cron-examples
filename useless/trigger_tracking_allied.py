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
              WHERE LOWER(`vx_freight_provider`)=%s \
              and `z_api_issue_update_flag_500`=%s and `z_lock_status`=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, ("allied", "1", "0"))
        booking_list = cursor.fetchall()

    # print('@10 - ', booking_list[0])
    # booking_list = Bookings.objects.filter(vx_freight_provider="Allied",
    #                                        z_api_issue_update_flag_500=1, b_client_name="Seaway",
    #                                        b_status_API__isnull=True)
    results = []

    for booking in booking_list:
        print("num : ", booking["pk_booking_id"])
        url = "http://35.161.204.104:8081/dme-api/tracking/trackconsignment"
        data = {}
        data["consignmentDetails"] = [
            {
                "consignmentNumber": booking["v_FPBookingNumber"],
                "destinationPostcode": booking["de_To_Address_PostalCode"],
            }
        ]
        data["spAccountDetails"] = {
            "accountCode": "DELVME",
            "accountState": "NSW",
            "accountKey": "ce0d58fd22ae8619974958e65302a715",
        }
        data["serviceProvider"] = "ALLIED"

        response0 = requests.post(url, params={}, json=data)
        response0 = response0.content.decode("utf8")
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual

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
                status_history_info = data0["consignmentTrackDetails"][0][
                    "consignmentStatuses"
                ][0]

                new_status = status_history_info["status"]
                event_time_stamp = None
                recipient_name = None

                if "statusDate" in status_history_info:
                    event_time_stamp = status_history_info["statusDate"]
                if "recipientName" in status_history_info:
                    recipient_name = status_history_info["recipientName"]

                print("status is fine.")
                if booking["b_status_API"] != new_status:
                    with mysqlcon.cursor() as cursor:
                        sql = "INSERT INTO `dme_status_history` (`fk_booking_id`, `status_old`, `notes`, `status_last`, \
                              `z_createdTimeStamp`, `event_time_stamp`, `recipient_name`, `status_update_via`) \
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
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
                                recipient_name,
                                "fp api",
                            ),
                        )
                        mysqlcon.commit()

                # total_Cubic_Meter_override = data0['consignmentTrackDetails'][0]['totalVolume']
                # total_1_KG_weight_override = data0['consignmentTrackDetails'][0]['totalWeight']
                # total_lines_qty_override = data0['consignmentTrackDetails'][0]['totalItems']
                with mysqlcon.cursor() as cursor:
                    sql = "SELECT * FROM `dme_utl_fp_statuses` \
                          WHERE LOWER(`fp_name`)=%s \
                          ORDER BY `id` ASC"
                    cursor.execute(sql, ("allied"))
                    fp_statuses = cursor.fetchall()

                    is_status_exist = False
                    ind = 0
                    for fp_status in fp_statuses:
                        if (
                            fp_status["fp_lookup_status"]
                            and fp_status["fp_lookup_status"] in new_status
                        ):
                            is_status_exist = True
                            break
                        ind = ind + 1

                    if not is_status_exist:
                        sql = "INSERT INTO `dme_utl_fp_statuses` \
                            (`fp_name`, `fp_original_status`, `fp_lookup_status`, `dme_status`) \
                            VALUES (%s, %s, %s, %s)"
                        cursor.execute(
                            sql,
                            ("Allied", new_status, new_status, "Pickup " + new_status),
                        )
                        mysqlcon.commit()
                        b_status = "api status"
                    else:
                        b_status = fp_statuses[ind]["dme_status"]

                    sql = "UPDATE `dme_bookings` \
                           SET b_status=%s, b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                           WHERE id=%s"
                    cursor.execute(
                        sql,
                        (b_status, new_status, datetime.datetime.now(), booking["id"]),
                    )
                    mysqlcon.commit()

                if new_status.lower() == "shipment has been delivered.":
                    with mysqlcon.cursor() as cursor:
                        sql = (
                            "Update `dme_bookings` set z_api_issue_update_flag_500=%s,"
                            "s_21_Actual_Delivery_TimeStamp=%s where id =%s"
                        )
                        cursor.execute(
                            sql,
                            (
                                "0",
                                data0["consignmentTrackDetails"][0][
                                    "scheduledDeliveryDate"
                                ],
                                booking["id"],
                            ),
                        )
                        mysqlcon.commit()

                with mysqlcon.cursor() as cursor:
                    sql = "SELECT * FROM `dme_client_warehouses` where pk_id_client_warehouses=%s"
                    cursor.execute(sql, (booking["fk_client_warehouse_id"]))
                    warehouse = cursor.fetchall()
                try:
                    if booking["z_pod_url"] is None or booking["z_pod_url"] == "":
                        print("now pod.")

                        pod_file = data0["consignmentTrackDetails"][0]["pods"][0][
                            "podData"
                        ]
                        print("pod is fine.")

                        warehouse_name = ""
                        if warehouse:
                            warehouse_name = warehouse[0]["client_warehouse_code"]
                        file_name = (
                            "POD_"
                            + str(warehouse_name)
                            + "_"
                            + booking["b_clientReference_RA_Numbers"]
                            + "_"
                            + booking["v_FPBookingNumber"]
                            + "_"
                            + str(booking["b_bookingID_Visual"])
                            + ".png"
                        )
                        file_url = "/opt/s3_public/imgs/" + file_name

                        with open(os.path.expanduser(file_url), "wb") as fout:
                            fout.write(base64.decodestring(pod_file.encode("utf-8")))

                        with mysqlcon.cursor() as cursor:
                            sql = "Update `dme_bookings` set z_pod_url=%s where id =%s"
                            cursor.execute(sql, (file_name, booking["id"]))
                            mysqlcon.commit()
                except IndexError:
                    print("POD : ", " empty")

                try:
                    if (
                        booking["z_pod_signed_url"] is None
                        or booking["z_pod_signed_url"] == ""
                    ):
                        print("now sign.")
                        pod_file = data0["consignmentTrackDetails"][0][
                            "consignmentStatuses"
                        ][0]["signatureImage"]
                        print("sign is fine.")
                        warehouse_name = ""
                        if warehouse:
                            warehouse_name = warehouse[0]["client_warehouse_code"]
                        file_name = (
                            "pod_signed_"
                            + str(warehouse_name)
                            + "_"
                            + booking["b_clientReference_RA_Numbers"]
                            + "_"
                            + booking["v_FPBookingNumber"]
                            + "_"
                            + str(booking["b_bookingID_Visual"])
                            + ".png"
                        )
                        file_url = "/opt/s3_public/imgs/" + file_name

                        with open(os.path.expanduser(file_url), "wb") as fout:
                            fout.write(base64.decodestring(pod_file.encode("utf-8")))

                        with mysqlcon.cursor() as cursor:
                            sql = "Update `dme_bookings` set z_pod_signed_url=%s where id =%s"
                            cursor.execute(sql, (file_name, booking["id"]))
                            mysqlcon.commit()
                except IndexError:
                    print("sign : ", " empty")

                try:
                    with mysqlcon.cursor() as cursor:
                        sql = "Update `dme_bookings` set vx_fp_pu_eta_time=%s, vx_fp_del_eta_time=%s, z_lastStatusAPI_ProcessedTimeStamp=%s where id =%s"
                        cursor.execute(
                            sql,
                            (
                                data0["consignmentTrackDetails"][0][
                                    "scheduledPickupDate"
                                ],
                                data0["consignmentTrackDetails"][0][
                                    "scheduledDeliveryDate"
                                ],
                                data0["consignmentTrackDetails"][0]["scannings"][0][
                                    "scanDate"
                                ],
                                booking["id"],
                            ),
                        )
                        mysqlcon.commit()
                except IndexError:
                    print("Delivery Date ", " no")

                print("success : ", booking["id"])
            except IndexError as e:
                print("error : ", booking["id"])
                print("error : ", e)
        except KeyError as e:
            print("error : ", e)
