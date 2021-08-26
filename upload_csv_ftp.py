# Python 3.7.0

import os, sys, time
import datetime
import pymysql, pymysql.cursors

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, CCO_DIR, CCO_ARCHIVE_DIR
from _options_lib import get_option, set_option
from _upload_download import upload_ftp

# CSV ftp server info
ftp_server_infos = [
    {
        # 'Century' server info
        "fp_name": "Century",
        # "host": "test.centurycouriers.com.au", # TEST usage
        "host": "ftp.centurycouriers.com.au",  # LIVE usage
        "username": "biopak",
        "password": "WiadOyn4",
        "ftp_filepath": "/input/",
        "local_filepath": CCO_DIR,
        "local_filepath_archive": CCO_ARCHIVE_DIR,
    }
]


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
        option = get_option(mysqlcon, "upload_csv_ftp")

        if int(option["option_value"]) == 0:
            print("#905 - `upload_csv_ftp` option is OFF")
        elif option["is_running"]:
            print("#905 - `upload_csv_ftp` script is already RUNNING")
        else:
            print("#906 - `upload_csv_ftp` option is ON")
            set_option(mysqlcon, "upload_csv_ftp", True)
            print("#910 - Processing...")

            try:
                for ftp_server_info in ftp_server_infos:
                    print(f"#901 - Running for `{ftp_server_info['fp_name']}`")

                    for fname in os.listdir(ftp_server_info["local_filepath"]):
                        fpath = os.path.join(ftp_server_info["local_filepath"], fname)

                        if (
                            os.path.isfile(fpath)
                            and fname.endswith(".csv")
                            and ftp_server_info["fp_name"] in fname
                        ):
                            print(f"#902 uploading: {fname}")
                            upload_ftp(
                                ftp_server_info["host"],
                                ftp_server_info["username"],
                                ftp_server_info["password"],
                                ftp_server_info["ftp_filepath"],
                                ftp_server_info["local_filepath"],
                                ftp_server_info["local_filepath_archive"],
                                fname,
                            )
            except OSError as e:
                print("Failed upload .CSV files to remote. Error: ", str(e))
                set_option(mysqlcon, "upload_csv_ftp", False, time1)

            print("#919 - Finished \o/")
            set_option(mysqlcon, "upload_csv_ftp", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "upload_csv_ftp", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
