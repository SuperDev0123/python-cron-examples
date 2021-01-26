# Python 3.7.0

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import pysftp

import _status_history
from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    HTC_REMOTE_DIR,
    HTC_REMOTE_ARCHIEV_DIR,
)
from _options_lib import get_option, set_option
from _upload_download import download_sftp, upload_sftp

# sftp server infos
sftp_server_infos = {
    "dme_hunter": {
        "type": "HQ",
        "name": "DELIVER_ME",
        "host": "3.105.62.128",
        "username": "hunteradmin",
        "password": "Admin4Hunt#123",
        "sftp_filepath": "/tracking/",
        "local_filepath": HTC_REMOTE_DIR,
        "local_filepath_archive": HTC_REMOTE_ARCHIEV_DIR,
    }
}

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

    try:
        option = get_option(mysqlcon, "hunter_status_pod_via_csv")

        if int(option["option_value"]) == 0:
            print("#905 - `hunter_status_pod_via_csv` option is OFF")
        elif option["is_running"]:
            print("#905 - `hunter_status_pod_via_csv` script is already RUNNING")
        else:
            print("#906 - `hunter_status_pod_via_csv` option is ON")
            set_option(mysqlcon, "hunter_status_pod_via_csv", True)
            print("#910 - Processing...")

            # Download .CSV files
            try:
                download_sftp(
                    sftp_server_infos["dme_hunter"]["host"],
                    sftp_server_infos["dme_hunter"]["username"],
                    sftp_server_infos["dme_hunter"]["password"],
                    sftp_server_infos["dme_hunter"]["sftp_filepath"],
                    sftp_server_infos["dme_hunter"]["local_filepath"],
                    sftp_server_infos["dme_hunter"]["local_filepath_archive"],
                )
            except OSError as e:
                print("Failed download .CSV files from remote. Error: ", str(e))
                set_option(mysqlcon, "hunter_status_pod_via_csv", False, time1)

            print("#919 - Finished \o/")
            set_option(mysqlcon, "hunter_status_pod_via_csv", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "hunter_status_pod_via_csv", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s" % datetime.datetime.now())
