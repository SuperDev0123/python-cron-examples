# Python 3.7.0

import sys, time
import json
import base64
from datetime import datetime
import pymysql, pymysql.cursors
import shutil
from os import listdir, path
import csv
import requests
import traceback

import _status_history
from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    HT_INPROGRESS_DIR as INPROGRESS_DIR,
    HT_ARCHIVE_DIR as ARCHIVE_DIR,
    HT_ISSUED_DIR as ISSUED_DIR,
    API_URL,
    S3_PUBLIC_URL,
    USERNAME,
    PASSWORD,
)
from _options_lib import get_option, set_option
from _upload_download import download_sftp, upload_sftp

# sftp server infos
sftp_server_infos = {
    "type": "Freight Provider",
    "name": "Hunter",
    "host": "3.24.213.204",
    "username": "dmeadmin",
    "password": "6FUB78AP4q@t",
    "sftp_filepath": "/transporter/status_tracking/",
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


def get_booking(consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_booking_id`, `vx_freight_provider`, `z_pod_url` From `dme_bookings` WHERE `v_FPBookingNumber`=%s AND lower(`vx_freight_provider`)=%s"
        cursor.execute(sql, (consignment_number, "hunter"))
        booking = cursor.fetchone()
    return booking


def update_booking(consignment_number, pod_url, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE dme_bookings SET z_pod_url=%s WHERE `v_FPBookingNumber`=%s"
        result = cursor.execute(sql, (pod_url, consignment_number))
    return result


def move_to_issued_dir(file):
    shutil.move(path.join(INPROGRESS_DIR, file), path.join(ISSUED_DIR, file))


def move_to_achived_dir(file):
    shutil.move(path.join(INPROGRESS_DIR, file), path.join(ARCHIVE_DIR, file))


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
        set_option(mysqlcon, "hunter_status_pod", False, time1)

    token = get_token()
    for file in listdir(INPROGRESS_DIR):

        if "ConsignmentStatusUpdate" in file:
            con_index = -1
            with open(path.join(INPROGRESS_DIR, file), "r") as csvfile:
                csv_content = list(csv.reader(csvfile))
                cols = csv_content[0]
                content = csv_content[1:]
                print("\nFile: ", file, "\nCols: ", cols, "\nContent: ", content)

                try:
                    con_index = cols.index("ConsignmentNumber")
                    time_index = cols.index("StatusDateTime")
                    status_index = cols.index("Status")
                except Exception as e:
                    print("Invalid format: ", file)
                    move_to_issued_dir(file)

                booking = None
                for index, line in enumerate(content):
                    consignment_number = line[con_index]
                    fp_status_code = line[status_index]
                    event_time_stamp = datetime.strptime(
                        line[time_index], "%d/%m/%Y %H:%M %z"
                    )
                    event_time_stamp_str = datetime.strptime(
                        line[time_index], "%d/%m/%Y %H:%M %z"
                    ).strftime("%Y-%m-%d %H:%M:%S.%f")

                    if event_time_stamp < datetime.strptime(
                        "2021-11-30 00:00 +11:00", "%Y-%m-%d %H:%M %z"
                    ):
                        print(f"Old tracking file: {file}, {event_time_stamp}")
                        move_to_issued_dir(file)

                    if not consignment_number:
                        print("No consignment number: ", file, ", Row: ", index + 1)
                        move_to_issued_dir(file)

                    if consignment_number:
                        booking = get_booking(consignment_number, mysqlcon)

                    if not booking:
                        print(
                            f"No booking or wrong freight_provider. file: {file}, Row: {index + 1}"
                        )
                        move_to_issued_dir(file)

                    if (
                        consignment_number
                        and booking
                        and booking["vx_freight_provider"]
                        and booking["vx_freight_provider"].lower() == "hunter"
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
                                    "fp_status": fp_status_code,
                                    "fp_status_description": None,
                                    "event_time_stamp": event_time_stamp_str,
                                    "is_from_script": True,
                                }
                            ),
                        )
        elif ".tif" in file or ".jpg" in file or ".png" in file:
            print(f"\n.tif file: {file}")
            consignment_number = file[:-4]
            booking = get_booking(consignment_number, mysqlcon)

            if booking and booking["z_pod_url"]:
                print(f"POD already exist - {consignment_number}")
            elif (
                booking
                and booking["vx_freight_provider"]
                and booking["vx_freight_provider"].lower() == "hunter"
                and not booking["z_pod_url"]
            ):
                full_path = f"{S3_PUBLIC_URL}/imgs/hunter_au/{file}"
                db_pod_url = f"hunter_au/{file}"
                shutil.move(path.join(INPROGRESS_DIR, file), full_path)
                result = update_booking(consignment_number, db_pod_url, mysqlcon)
                print(f"Set POD: {full_path}")
            else:
                print("No booking or wrong freight_provider: ", file)
                move_to_issued_dir(file)

        move_to_achived_dir(file)


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
        option = get_option(mysqlcon, "hunter_status_pod")

        if int(option["option_value"]) == 0:
            print("#905 - `hunter_status_pod` option is OFF")
        elif option["is_running"]:
            print("#905 - `hunter_status_pod` script is already RUNNING")
        else:
            print("#906 - `hunter_status_pod` option is ON")
            set_option(mysqlcon, "hunter_status_pod", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "hunter_status_pod", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        traceback.print_exc()
        set_option(mysqlcon, "hunter_status_pod", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.now())
