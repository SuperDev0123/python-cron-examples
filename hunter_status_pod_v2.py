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

import _status_history
from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    HUNTER_FTP_DIR as FTP_DIR,
    HUNTER_ARCHIVE_FTP_DIR as ARCHIVE_FTP_DIR,
    HUNTER_ISSUED_FTP_DIR as ISSUED_FTP_DIR,
    API_URL
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
    "local_filepath": FTP_DIR,
    "local_filepath_archive": ARCHIVE_FTP_DIR,
}


def update_booking(consignment_number, pod_url, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE dme_bookings SET z_pod_url=%s WHERE `v_FPBookingNumber`=%s"
        result = cursor.execute(sql, (pod_url, consignment_number))
    return result

def get_booking(consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `vx_freight_provider` From `dme_bookings` WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (consignment_number))
        booking = cursor.fetchone()
    return booking
        
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

    if not path.isdir(FTP_DIR) or not path.isdir(ARCHIVE_FTP_DIR):
        print('Given argument "%s, %s" is not a directory' % FTP_DIR, ARCHIVE_FTP_DIR)
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

            Download .FTP files
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


            for file in listdir(FTP_DIR):
                response = None
                have_issue = False
                should_archive = False
                if 'ConsignmentStatusUpdate' in file:
                    con_index = -1
                    with open(path.join(FTP_DIR, file), 'r') as csvfile:
                        csv_content = list(csv.reader(csvfile))
                        try:
                            header = csv_content[0]
                            con_index = header.index('ConsignmentNumber')
                            time_index = header.index('StatusDateTime')
                            status_index = header.index('Status')
                        except Exception as e:
                            have_issue = True
                            print('Invalid file type: ', file)
                    if con_index == 0:
                        content = csv_content[1:]
                        for index, line in enumerate(content):
                            consignment_number = line[con_index]
                            fp_status_code = line[status_index]
                            event_time_stamp = datetime.strptime(line[time_index], '%d/%m/%Y %H:%M %z').strftime('%Y-%m-%d %H:%M:%S.%f')

                            if consignment_number:
                                booking = get_booking(consignment_number, mysqlcon)
                            else:
                                print('No consignment number: ', file, ', Row: ', index + 1)
                                have_issue = True

                            if booking and booking['vx_freight_provider'].lower() == 'hunter':
                                headers = {
                                    "content-type": "application/json",
                                }
                                response = requests.post(f"{API_URL}/statushistory/save_status_history/", headers=headers, data=json.dumps({
                                    'booking_id': booking['id'],
                                    'consignment_number': consignment_number,
                                    'fp_status_code': fp_status_code,
                                    'fp_status_details': None,
                                    'event_time_stamp': event_time_stamp,
                                    'is_from_script': True
                                }))
                                if response and response.ok:
                                    should_archive = True
                            else:
                                print('No booking or wrong freight_provider: ', file, ', Row: ', index + 1)
                                have_issue = True
                elif 'Pod' in file:
                    with open(path.join(FTP_DIR, file), 'r') as csvfile:
                        csv_content = list(csv.reader(csvfile))
                        row_count = len(csv_content)
                        for index in range(1, row_count):
                            consignment_number = csv_content[index][0]
                            image = csv_content[index][8]
                        
                            if consignment_number:
                                booking = get_booking(consignment_number, mysqlcon)
                            else:
                                print('No Consignment number: ', file, 'row: ', index)
                                have_issue = True
                            
                            if booking and booking['vx_freight_provider'].lower() == 'hunter':
                                full_path = f"{S3_URL}/pdfs/hunter_au/{consignment_number}.tif"
                                db_pod_url = f"hunter_au/{consignment_number}.tif"
                                with open(full_path, "wb") as f:
                                    f.write(base64.b64decode(image))
                                    f.close()
                                    update_booking(consignment_number, db_pod_url, mysqlcon)

                            else:
                                print('No booking or wrong freight_provider: ', file, 'row: ', index)
                                have_issue = True
                        if not have_issue:
                            should_archive = True
                if have_issue:
                    shutil.move(path.join(FTP_DIR, file), path.join(ISSUED_FTP_DIR, file))
                elif should_archive:
                    shutil.move(path.join(FTP_DIR, file), path.join(ARCHIVE_FTP_DIR, file))

            set_option(mysqlcon, "hunter_status_pod", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "hunter_status_pod", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.now())
