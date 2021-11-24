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
    USERNAME,
    PASSWORD,
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


def get_booking(booking_id, consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        if booking_id:
            sql = "SELECT `id`, `pk_booking_id`, `vx_freight_provider` From `dme_bookings` WHERE `id`=%s"
            cursor.execute(sql, (booking_id))
            booking = cursor.fetchone()
        else:
            sql = "SELECT `id`, `pk_booking_id`, `vx_freight_provider` From `dme_bookings` WHERE `v_FPBookingNumber`=%s"
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

    token = get_token()
    for file in listdir(INPROGRESS_DIR):
        response = None
        has_issue = False
        with open(path.join(INPROGRESS_DIR, file), "r") as csvfile:
            booking_id = None
            csv_list = list(csv.reader(csvfile))
            cols = csv_list[0]
            content = csv_list[1]
            print("\nFile: ", file, "\nCols: ", cols, "\nContent: ", content)

            if cols[0] == "customer_order_number":
                consignment_number = content[-1]
                fp_status = content[3]
                fp_status_description = content[5]
                event_time_stamp = datetime.strptime(content[2], "%Y%m%d").strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )
            else:
                consignment_number = content[-1]
                fp_status = content[2]
                fp_status_description = content[4]
                event_time_stamp = datetime.strptime(content[1], "%Y%m%d").strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )

            print(f"consignment_number: {consignment_number}")

            if not booking_id and not consignment_number:
                print("No booking id and consignment number: ", file)
                has_issue = True
            else:
                booking = get_booking(booking_id, consignment_number, mysqlcon)

                if (
                    booking
                    and booking["vx_freight_provider"]
                    and booking["vx_freight_provider"].lower() == "century"
                ):
                    headers = {
                        "content-type": "application/json",
                        "Authorization": f"JWT {token}",
                    }
                    response = requests.post(
                        f"{API_URL}/statushistory/save_status_history/",
                        headers=headers,
                        data=json.dumps(
                            {
                                "fk_booking_id": booking["pk_booking_id"],
                                "consignment_number": consignment_number,
                                "fp_status": fp_status,
                                "fp_status_description": fp_status_description,
                                "event_time_stamp": event_time_stamp,
                                "is_from_script": True,
                            }
                        ),
                    )
                    has_issue = response.status_code != 200
                    break
                else:
                    print("No booking or wrong freight_provider: ", file)
                    has_issue = True

        if has_issue:
            shutil.move(path.join(INPROGRESS_DIR, file), path.join(ISSUED_DIR, file))
        else:
            shutil.move(path.join(INPROGRESS_DIR, file), path.join(ARCHIVE_DIR, file))


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
