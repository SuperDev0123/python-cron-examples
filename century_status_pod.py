# Python 3.7.0

import sys, time
import json
import datetime
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
    CENTURY_FTP_DIR as FTP_DIR,
    CENTURY_ARCHIVE_FTP_DIR as ARCHIVE_FTP_DIR,
    # ST_CSV_DIR as CSV_DIR,
    # ST_ARCHIVE_CSV_DIR as ARCHIVE_CSV_DIR,
    API_URL
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
    "local_filepath": FTP_DIR,
    "local_filepath_archive": ARCHIVE_FTP_DIR,
}

def get_dme_status(fp_status, mysqlcon):
    try:
        with mysqlcon.cursor() as cursor:
            sql = "SELECT `dme_status` FROM `dme_utl_fp_statuses` WHERE `fp_name`=`CENTURY` AND `fp_lookup_status`=%s"
            cursor.execute(sql, (fp_status))
            status = cursor.fetchone()
            return status['dme_status']
    except:
        return None

        
def get_booking(consignment_number, mysqlcon):
    try:
        with mysqlcon.cursor() as cursor:
            sql = "SELECT `id`, `b_bookingID_Visual`, `pk_booking_id`, `b_status`, `b_status_API` \
                    From `dme_bookings` \
                    WHERE `v_FPBookingNumber`=%s"
            cursor.execute(sql, (consignment_number))
            booking = cursor.fetchone()

            return booking
    except:
        return None


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())
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

    if not path.isdir(FTP_DIR) or not path.isdir(CSV_DIR):
        print('Given argument "%s, %s" is not a directory' % FTP_DIR, CSV_DIR)
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
        
            for file in listdir(FTP_DIR):
                response = None
                with open(path.join(FTP_DIR, file), 'r') as csvfile:
                    csvreader = csv.reader(csvfile)
                    content = list(csvreader)[1]
                    consignment_number = content[1]
                    fp_status_code = content[3]
                    notes = content[5]
                    event_time_stamp = content[2]

                    booking = get_booking(consignment_number, mysqlcon)
                    if booking:
                        status_last = get_dme_status(fp_status_code, mysqlcon)
                        response = requests.post(f"{API_URL}/statushistory/create", data=json.dumps({
                            'fk_booking_id': booking['pk_booking_id'],
                            'status_last': status_last,
                            'event_time_stamp': event_time_stamp
                        }))

                if response and response.ok:
                    shutil.move(path.join(FTP_DIR, file), path.join(ARCHIVE_FTP_DIR, file)) 

            
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "century_status_pod", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
