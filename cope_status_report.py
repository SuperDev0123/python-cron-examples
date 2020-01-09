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

import _status_history

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


def get_v_FPBookingNumber(v_FPBookingNumber):
    # if "_" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("_", "")
    # if "-" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("-", "")

    return v_FPBookingNumber


def get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_dateBookedDate`, `b_status`, `b_status_API`, `pk_booking_id`, \
                      `e_qty_scanned_fp_total`, `z_lock_status`, `pu_Address_PostalCode`, \
                      `de_To_Address_PostalCode`, `b_bookingID_Visual`, `tally_delivered`, \
                      `fp_received_date_time`, `b_given_to_transport_date_time`, `delivery_kpi_days`, \
                      `dme_status_detail_updated_by`, `dme_status_detail` \
                FROM `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (v_FPBookingNumber))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result


def calc_delivered(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        tally_delivered = booking["tally_delivered"]

        if not tally_delivered:
            tally_delivered = 0

        sql = "UPDATE `dme_bookings` \
                SET `tally_delivered`=%s \
                WHERE `id`=%s"
        cursor.execute(sql, (int(tally_delivered) + 1, booking["id"]))
        mysqlcon.commit()

        sql = "SELECT `pk_lines_id`, `e_qty`, `e_qty_awaiting_inventory`, `e_qty_delivered` \
                FROM `dme_booking_lines` \
                WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (booking["pk_booking_id"]))
        booking_lines = cursor.fetchall()

        for booking_line in booking_lines:
            if not booking_line["e_qty"]:
                booking_line["e_qty"] = 0
            if not booking_line["e_qty_awaiting_inventory"]:
                booking_line["e_qty_awaiting_inventory"] = 0

            booking_line["e_qty_delivered"] = int(booking_line["e_qty"]) - int(
                booking_line["e_qty_awaiting_inventory"]
            )

            sql = "UPDATE `dme_booking_lines` \
                    SET `e_qty_delivered`=%s \
                    WHERE `pk_lines_id`=%s"
            cursor.execute(
                sql, (booking_line["e_qty_delivered"], booking_line["pk_lines_id"])
            )
            mysqlcon.commit()


def update_booking(booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
               SET b_status=%s, b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s, \
                    dme_status_detail=%s, dme_status_action=%s \
               WHERE id=%s"
        cursor.execute(
            sql,
            (
                b_status,
                b_status_API_csv,
                datetime.datetime.now(),
                "",
                "",
                booking["id"],
            ),
        )
        mysqlcon.commit()

        if b_status == "In Transit" and (
            not booking["dme_status_detail_updated_by"]
            or booking["dme_status_detail_updated_by"] == "script"
        ):
            if (
                booking["b_given_to_transport_date_time"]
                and not booking["fp_received_date_time"]
            ):
                sql = "UPDATE `dme_bookings` \
                    SET dme_status_detail=%s, prev_dme_status_detail=%s, dme_status_detail_updated_at=%s, \
                        dme_status_detail_updated_by=%s \
                    WHERE `id`=%s"
                cursor.execute(
                    sql,
                    (
                        "Collection Confirmed by Pickup Address",
                        booking["dme_status_detail"],
                        datetime.datetime.now(),
                        "script",
                        booking["id"],
                    ),
                )
            # if booking["fp_received_date_time"]:
            #     sql = "UPDATE `dme_bookings` \
            #         SET dme_status_detail=%s, prev_dme_status_detail=%s, dme_status_detail_updated_at=%s, \
            #             dme_status_detail_updated_by=%s \
            #         WHERE `id`=%s"
            #     cursor.execute(
            #         sql,
            #         (
            #             "Good Received by Transport",
            #             booking["dme_status_detail"],
            #             datetime.datetime.now(),
            #             "script",
            #             booking["id"],
            #         ),
            #     )
            mysqlcon.commit()
        elif b_status == "Delivered":
            sql = "UPDATE `dme_bookings` \
                    SET dme_status_detail=%s, prev_dme_status_detail=%s, dme_status_detail_updated_at=%s, \
                        dme_status_detail_updated_by=%s \
                    WHERE `id`=%s"
            cursor.execute(
                sql,
                (
                    "",
                    booking["dme_status_detail"],
                    datetime.datetime.now(),
                    "script",
                    booking["id"],
                ),
            )
            mysqlcon.commit()


def do_translate_status(
    booking,
    b_status_API_csv,
    v_FPBookingNumber,
    event_time_stamp,
    b_fp_qty_delivered_csv,
    mysqlcon,
    is_overridable=False,
):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
              WHERE LOWER(`fp_name`)=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, ("cope"))
        fp_statuses = cursor.fetchall()

        ind = 0
        for fp_status in fp_statuses:
            if (
                fp_status["fp_lookup_status"]
                and fp_status["fp_lookup_status"] in b_status_API_csv
            ):
                break
            ind = ind + 1

        b_status = fp_statuses[ind]["dme_status"]
        is_status = fp_statuses[ind]["if_scan_total_in_booking_greaterthanzero"]

        if is_overridable:
            update_booking(
                booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon
            )
            _status_history.create(booking["id"], None, event_time_stamp, b_status)
        else:
            if (
                booking["e_qty_scanned_fp_total"]
                and booking["e_qty_scanned_fp_total"] > 0
            ):
                b_status = is_status
                update_booking(
                    booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon
                )
                _status_history.create(booking["id"], None, event_time_stamp, b_status)
            else:
                update_booking(
                    booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon
                )
                _status_history.create(booking["id"], None, event_time_stamp, b_status)

        if "Proof of Delivery" in b_status_API_csv:
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

            delivery_kpi_days = result["delivery_days"] if result else 14

            if not booking["b_dateBookedDate"]:
                sql = "UPDATE `dme_bookings` \
                   SET b_error_Capture = %s \
                   WHERE id=%s"
                cursor.execute(sql, ("Delivered but no booked date", booking["id"]))
                mysqlcon.commit()
            else:
                delivery_days_from_booked = (
                    event_time_stamp - booking["b_dateBookedDate"]
                ).days
                delivery_actual_kpi_days = delivery_days_from_booked - delivery_kpi_days

                sql = "UPDATE `dme_bookings` \
                   SET s_21_ActualDeliveryTimeStamp=%s, delivery_kpi_days=%s, \
                       delivery_days_from_booked=%s, delivery_actual_kpi_days=%s, \
                       rpt_proof_of_del_from_csv_time=%s, b_fp_qty_delivered=%s \
                   WHERE id=%s"
                cursor.execute(
                    sql,
                    (
                        event_time_stamp,
                        delivery_kpi_days,
                        delivery_days_from_booked,
                        delivery_actual_kpi_days,
                        datetime.datetime.now(),
                        b_fp_qty_delivered_csv,
                        booking["id"],
                    ),
                )
                mysqlcon.commit()

                calc_delivered(booking, mysqlcon)


def is_b_status_API_csv(booking, b_status_API_csv, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
                WHERE LOWER(`fp_name`)=%s"
        cursor.execute(sql, ("cope"))
        fp_statuses = cursor.fetchall()

        is_new = True
        for fp_status in fp_statuses:
            if (
                fp_status["fp_lookup_status"]
                and fp_status["fp_lookup_status"] in b_status_API_csv
            ):
                is_new = False
                break

        return is_new


def is_overridable(b_status_API_csv, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
              WHERE `pod_delivery_override`=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, (1))
        fp_statuses = cursor.fetchall()

        bool_val = False
        for fp_status in fp_statuses:
            if fp_status["fp_original_status"] == b_status_API_csv:
                bool_val = True
                break

        return bool_val


def update_status(fpath, mysqlcon):
    with open(fpath) as csv_file:
        with mysqlcon.cursor() as cursor:
            for i, line in enumerate(csv_file):
                v_FPBookingNumber = get_v_FPBookingNumber(line.split(",")[0])
                # new_v_FPBookingNumber = v_FPBookingNumber.replace("DME", "DME_")
                b_status_API_csv = line.split(",")[1].replace('"', "")
                b_fp_qty_delivered_csv = line.split(",")[2]

                if "-" in line.split(",")[3]:
                    event_time_stamp = datetime.datetime.strptime(
                        line.split(",")[3] + " " + line.split(",")[4].replace("\n", ""),
                        "%Y-%m-%d %H:%M",
                    )
                else:
                    event_time_stamp = datetime.datetime.strptime(
                        line.split(",")[3] + " " + line.split(",")[4].replace("\n", ""),
                        "%d/%m/%y %H:%M",
                    )

                booking = get_booking_with_v_FPBookingNumber(
                    v_FPBookingNumber, mysqlcon
                )

                if not booking:
                    print("@102 v_FPBookingNumber not match: ", v_FPBookingNumber)
                else:
                    print(
                        "@103 v_FPBookingNumber match: ",
                        v_FPBookingNumber,
                        event_time_stamp,
                    )

                    if is_b_status_API_csv(booking, b_status_API_csv, mysqlcon):
                        sql = "UPDATE `dme_bookings` \
                               SET z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                               WHERE id=%s"
                        cursor.execute(
                            sql,
                            (
                                "New Status from FP ("
                                + b_status_API_csv
                                + ") "
                                + str(datetime.datetime.now().strftime("%d/%m/%Y")),
                                datetime.datetime.now(),
                                booking["id"],
                            ),
                        )
                        mysqlcon.commit()
                    else:
                        if booking["z_lock_status"]:
                            if (
                                is_overridable(b_status_API_csv, mysqlcon)
                                and booking["b_status_API"] == b_status_API_csv
                            ):
                                print("@70 - ")
                                sql = "UPDATE `dme_bookings` \
                                       SET z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(
                                    sql,
                                    (
                                        "status was locked with ("
                                        + booking["b_status"]
                                        + ") - POD Received not set",
                                        datetime.datetime.now(),
                                        booking["id"],
                                    ),
                                )
                                mysqlcon.commit()
                            else:
                                print("@71 - ")
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(
                                    sql,
                                    (
                                        b_status_API_csv,
                                        "status was locked with ("
                                        + booking["b_status"]
                                        + ") - api status changed but not b_status",
                                        datetime.datetime.now(),
                                        booking["id"],
                                    ),
                                )
                                mysqlcon.commit()
                            # create_status_history(booking, 'Locked', event_time_stamp, mysqlcon)
                        else:
                            if (
                                booking["b_status_API"] == "POD Received"
                                and is_overridable(b_status_API_csv, mysqlcon)
                                and booking["b_status_API"] != b_status_API_csv
                            ):
                                print("@80 - ")
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(
                                    sql,
                                    (
                                        b_status_API_csv,
                                        datetime.datetime.now(),
                                        booking["id"],
                                    ),
                                )
                                mysqlcon.commit()
                                do_translate_status(
                                    booking,
                                    b_status_API_csv,
                                    v_FPBookingNumber,
                                    event_time_stamp,
                                    b_fp_qty_delivered_csv,
                                    mysqlcon,
                                    True,
                                )
                            elif (
                                booking["b_status_API"] != "POD Received"
                                and booking["b_status_API"] != b_status_API_csv
                            ):
                                print("@81 - ")
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(
                                    sql,
                                    (
                                        b_status_API_csv,
                                        datetime.datetime.now(),
                                        booking["id"],
                                    ),
                                )
                                mysqlcon.commit()
                                do_translate_status(
                                    booking,
                                    b_status_API_csv,
                                    v_FPBookingNumber,
                                    event_time_stamp,
                                    b_fp_qty_delivered_csv,
                                    mysqlcon,
                                    False,
                                )
                            else:
                                print("@82 - ")
                                sql = "UPDATE `dme_bookings` \
                                       SET z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(
                                    sql, (datetime.datetime.now(), booking["id"])
                                )
                                mysqlcon.commit()


def do_status_check(mysqlcon):
    with mysqlcon.cursor() as cursor:
        # for all bookings that have a b_stauts = entered or booked only, as per below
        #    1. b_status to 'In Transit' if qty scanned = qty booked
        #    2. b_status to 'In Transit' if qty scanned < qty booked but not Null or 0 and set Status Detail to 'In transporter's depot (partial)'
        sql = "SELECT `id`, `pk_booking_id`, `e_qty_scanned_fp_total` \
                From `dme_bookings` \
                WHERE `b_status`=%s or `b_status`=%s"
        cursor.execute(sql, ("Entered", "Booked"))
        bookings = cursor.fetchall()

        for booking in bookings:
            sql = "SELECT `pk_lines_id`, `e_qty` \
                    From `dme_booking_lines` \
                    WHERE `fk_booking_id`=%s"
            cursor.execute(sql, (booking["pk_booking_id"]))
            booking_lines = cursor.fetchall()

            e_qty_total = 0

            for booking_line in booking_lines:
                if booking_line["e_qty"] is not None:
                    e_qty_total += booking_line["e_qty"]

            if (
                booking["e_qty_scanned_fp_total"] != 0
                and booking["e_qty_scanned_fp_total"] is not None
            ) and booking["e_qty_scanned_fp_total"] == e_qty_total:
                sql = "UPDATE `dme_bookings` \
                       SET b_status=%s, z_ModifiedTimestamp=%s \
                       WHERE id=%s"
                cursor.execute(
                    sql, ("In Transit", datetime.datetime.now(), booking["id"])
                )
                mysqlcon.commit()
            elif (
                booking["e_qty_scanned_fp_total"] is not None
                and (
                    booking["e_qty_scanned_fp_total"] != 0
                    and booking["e_qty_scanned_fp_total"] is not None
                )
                and booking["e_qty_scanned_fp_total"] < e_qty_total
                and booking["e_qty_scanned_fp_total"] > 0
            ):
                sql = "UPDATE `dme_bookings` \
                       SET b_status=%s, dme_status_detail=%s, z_ModifiedTimestamp=%s, \
                           prev_dme_status_detail=%s, dme_status_detail_updated_at=%s, \
                           dme_status_detail_updated_by=%s \
                       WHERE id=%s"
                cursor.execute(
                    sql,
                    (
                        "In Transit",
                        "In transporter's depot (partial)",
                        datetime.datetime.now(),
                        booking["dme_status_detail"],
                        datetime.datetime.now(),
                        "script",
                        booking["id"],
                    ),
                )
                mysqlcon.commit()

        # POD Check
        #     1. If a POD exists and scans equal the qty booked set b_status to Delivered
        #     2. If a POD exists and scans are less than the qty booked set b_status to 'Delivered' and Satus Detail to 'Delivered Partial'
        #     3. if a POD exists and scans are 0 or NULL, set b_status to 'POD Check Required'
        sql = "SELECT `id`, `pk_booking_id`, `e_qty_scanned_fp_total`, `z_pod_signed_url` \
                From `dme_bookings` \
                WHERE `id`=%s"
        cursor.execute(sql, ("23199"))
        bookings = cursor.fetchall()

        for booking in bookings:
            sql = "SELECT `pk_lines_id`, `e_qty` \
                    From `dme_booking_lines` \
                    WHERE `fk_booking_id`=%s"
            cursor.execute(sql, (booking["pk_booking_id"]))
            booking_lines = cursor.fetchall()

            e_qty_total = 0

            for booking_line in booking_lines:
                if booking_line["e_qty"] is not None:
                    e_qty_total += booking_line["e_qty"]

            if (
                (
                    booking["z_pod_signed_url"] is not None
                    and booking["z_pod_signed_url"] != ""
                )
                and (
                    booking["e_qty_scanned_fp_total"] != 0
                    and booking["e_qty_scanned_fp_total"] is not None
                )
                and booking["e_qty_scanned_fp_total"] == e_qty_total
            ):
                sql = "UPDATE `dme_bookings` \
                       SET b_status=%s, z_ModifiedTimestamp=%s \
                       WHERE id=%s"
                cursor.execute(
                    sql, ("Delivered", datetime.datetime.now(), booking["id"])
                )
                mysqlcon.commit()
            elif (
                (
                    booking["z_pod_signed_url"] is not None
                    and booking["z_pod_signed_url"] != ""
                )
                and (
                    booking["e_qty_scanned_fp_total"] != 0
                    and booking["e_qty_scanned_fp_total"] is not None
                )
                and booking["e_qty_scanned_fp_total"] < e_qty_total
            ):
                sql = "UPDATE `dme_bookings` \
                       SET b_status=%s, dme_status_detail=%s, z_ModifiedTimestamp=%s, \
                           prev_dme_status_detail=%s, dme_status_detail_updated_at=%s, \
                           dme_status_detail_updated_by=%s \
                       WHERE id=%s"
                cursor.execute(
                    sql,
                    (
                        "Delivered",
                        "Delivered Partial",
                        datetime.datetime.now(),
                        booking["dme_status_detail"],
                        datetime.datetime.now(),
                        "script",
                        booking["id"],
                    ),
                )
                mysqlcon.commit()
            elif (
                booking["z_pod_signed_url"] is not None
                and booking["z_pod_signed_url"] != ""
            ) and (
                booking["e_qty_scanned_fp_total"] == 0
                or booking["e_qty_scanned_fp_total"] is None
            ):
                sql = "UPDATE `dme_bookings` \
                       SET b_status=%s, dme_status_detail=%s, z_ModifiedTimestamp=%s \
                       WHERE id=%s"
                cursor.execute(
                    sql,
                    (
                        "Delivered",
                        "POD Check Required",
                        datetime.datetime.now(),
                        booking["id"],
                    ),
                )
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

    if production:
        CSV_DIR = "/home/cope_au/dme_sftp/cope_au/tracking_status/indata/"
        ARCHIVE_DIR = "/home/cope_au/dme_sftp/cope_au/tracking_status/archive/"
    else:
        CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
        ARCHIVE_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

    if not os.path.isdir(CSV_DIR):
        print('Given argument "%s" is not a directory' % CSV_DIR)
        exit(1)

    try:
        for fname in os.listdir(CSV_DIR):
            fpath = os.path.join(CSV_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".csv"):
                print("@100 Detect csv file:", fpath)
                update_status(fpath, mysqlcon)
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print("@109 Moved csv file:", fpath)

    except OSError as e:
        print("#902 Error", str(e))

    try:
        do_status_check(mysqlcon)
    except OSError as e:
        print("#903 Error", str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
