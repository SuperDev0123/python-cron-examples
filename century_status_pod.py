# Python 3.7.0

import sys, time
import json
from datetime import datetime
import pymysql, pymysql.cursors
import shutil
from os import listdir, path
import csv
import requests

import _status_history
from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    CTC_INPROGRESS_DIR as INPROGRESS_DIR,
    CTC_ARCHIVE_DIR as ARCHIVE_DIR,
    CTC_ISSUED_DIR as ISSUED_DIR,
    API_URL,
)
from _options_lib import get_option, set_option
from _upload_download import download_sftp, upload_sftp

# sftp server infos
sftp_server_infos = {
    "type": "Freight Provider",
    "name": "Century",
    "host": "3.24.213.204",
    "username": "dmeadmin",
    "password": "6FUB78AP4q@t",
    "sftp_filepath": "/transporter/status_tracking/indata/",
    "local_filepath": INPROGRESS_DIR,
    "local_filepath_archive": ARCHIVE_DIR,
}


def get_booking(booking_id, consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        if booking_id:
            sql = "SELECT `id`, `vx_freight_provider` From `dme_bookings` WHERE `id`=%s"
            cursor.execute(sql, (booking_id))
            booking = cursor.fetchone()
        else:
            sql = "SELECT `id`, `vx_freight_provider` From `dme_bookings` WHERE `v_FPBookingNumber`=%s"
            cursor.execute(sql, (consignment_number))
            booking = cursor.fetchone()
        return booking


def do_process(mysqlcon):
    # Download .FTP files
    try:
        download_sftp(
            sftp_server_infos["host"],
            sftp_server_infos["username"],
            sftp_server_infos["password"],
            sftp_server_infos["sftp_filepath"],
            sftp_server_infos["local_filepath"],
            sftp_server_infos["local_filepath_archive"],
        )
    except OSError as e:
        print("Failed download .FTP files from remote. Error: ", str(e))
        set_option(mysqlcon, "century_status_pod", False, time1)

    for file in listdir(INPROGRESS_DIR):
        response = None
        should_issue = False
        with open(path.join(INPROGRESS_DIR, file), "r") as csvfile:
            csv_list = list(csv.reader(csvfile))
            cols = csv_list[0]
            content = csv_list[1]

            print("\n@1 - ", file, "\n", cols, "\n", content)

            if "booking_number" in cols:
                index = cols.index("booking_number")
                booking_id = content[index]
            else:
                booking_id = None

            if cols[0] == "customer_order_number":
                consignment_number = content[1]
                fp_status_code = content[3]
                fp_status_details = content[5]
                event_time_stamp = datetime.strptime(content[2], "%Y%m%d").strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )
            else:
                consignment_number = content[0]
                fp_status_code = content[2]
                fp_status_details = content[4]
                event_time_stamp = datetime.strptime(content[1], "%Y%m%d").strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )

            if not booking_id and not consignment_number:
                print("No booking id and consignment number: ", file)
                should_issue = True
            else:
                booking = get_booking(booking_id, consignment_number, mysqlcon)
                if (
                    booking
                    and booking["vx_freight_provider"]
                    and booking["vx_freight_provider"].lower() == "century"
                ):
                    # headers = {"content-type": "application/json"}
                    # response = requests.post(
                    #     f"{API_URL}/statushistory/save_status_history/",
                    #     headers=headers,
                    #     data=json.dumps(
                    #         {
                    #             "booking_id": booking["id"],
                    #             "consignment_number": consignment_number,
                    #             "fp_status_code": fp_status_code,
                    #             "fp_status_details": fp_status_details,
                    #             "event_time_stamp": event_time_stamp,
                    #             "is_from_script": True,
                    #         }
                    #     ),
                    # )
                    print(
                        "@! - ",
                        {
                            "booking_id": booking["id"],
                            "consignment_number": consignment_number,
                            "fp_status_code": fp_status_code,
                            "fp_status_details": fp_status_details,
                            "event_time_stamp": event_time_stamp,
                            "is_from_script": True,
                        },
                    )
                else:
                    print("No booking or wrong freight_provider: ", file)
                    should_issue = True

        # if response and response.ok:
        #     shutil.move(path.join(INPROGRESS_DIR, file), path.join(ARCHIVE_DIR, file))
        # if should_issue:
        #     shutil.move(path.join(INPROGRESS_DIR, file), path.join(ISSUED_DIR, file))


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

    if not path.isdir(INPROGRESS_DIR):
        print(f"{INPROGRESS_DIR} is not a directory")
        exit(1)

    if not path.isdir(ARCHIVE_DIR):
        print(f"{ARCHIVE_DIR} is not a directory")
        exit(1)

    try:
        option = get_option(mysqlcon, "century_status_pod")

        if int(option["option_value"]) == 0:
            print("#905 - `century_status_pod` option is OFF")
        elif option["is_running"]:
            print("#905 - `century_status_pod` script is already RUNNING")
        else:
            print("#906 - `century_status_pod` option is ON")
            set_option(mysqlcon, "century_status_pod", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "century_status_pod", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "century_status_pod", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.now())
