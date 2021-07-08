# Python 3.7.0

import os, sys, time
import datetime
import pymysql, pymysql.cursors

from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    STTCO_DIR,
    STTCO_ARCHIVE_DIR,
)
from _options_lib import get_option, set_option
from _upload_download import upload_sftp

# CSV sftp server info
sftp_server_infos = [
    # {
    #     "fp_name": "Cope",
    #     "host": "esmart.cope.com.au",
    #     "username": "deliverme",
    #     "password": "C3n?7u4f",
    #     "sftp_filepath": "/home/import/csvimport/upload/",
    #     "local_filepath": "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/",
    #     "local_filepath_archive": "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/archive/",
    # },
    # {
    #     # DHL QA(test) server info
    #     "fp_name": "DHL",
    #     "host": "ftp2-dhllink-qa.dhl.com",
    #     "username": "deliverme_au_tst_sftp",
    #     "password": "Rbk3Zxi605_5YCIU",
    #     "sftp_filepath": "/in/",
    #     "local_filepath": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/",
    #     "local_filepath_archive": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/archive/",
    # },
    # {
    #     # DHL PROD server info
    #     "fp_name": "DHL",
    #     "host": "ftp2-dhllink.dhl.com",
    #     "username": "deliverme_au_sftp",
    #     "password": "O2hdByBe1qWhAcrq",
    #     "sftp_filepath": "/in/",
    #     "local_filepath": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/",
    #     "local_filepath_archive": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/archive/",
    # },
    {
        # 'State Transport' PROD server info
        "fp_name": "State Transport",
        "host": "batchprocessing.hubsystems.com.au",
        "username": "state-deliverme",
        "password": "Wp#S8Y:x^Dgc7",
        "sftp_filepath": "/in/",
        "local_filepath": STTCO_DIR,
        "local_filepath_archive": STTCO_ARCHIVE_DIR,
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
        option = get_option(mysqlcon, "upload_csv_sftp")

        if int(option["option_value"]) == 0:
            print("#905 - `upload_csv_sftp` option is OFF")
        elif option["is_running"]:
            print("#905 - `upload_csv_sftp` script is already RUNNING")
        else:
            print("#906 - `upload_csv_sftp` option is ON")
            set_option(mysqlcon, "upload_csv_sftp", True)
            print("#910 - Processing...")

            try:
                for sftp_server_info in sftp_server_infos:
                    print(f"#901 - Running for `{sftp_server_info['fp_name']}`")

                    for fname in os.listdir(sftp_server_info["local_filepath"]):
                        fpath = os.path.join(sftp_server_info["local_filepath"], fname)

                        if (
                            os.path.isfile(fpath)
                            and fname.endswith(".csv")
                            and sftp_server_info["fp_name"] in fname
                        ):
                            print(f"#902 uploading: {fname}")
                            upload_sftp(
                                sftp_server_info["host"],
                                sftp_server_info["username"],
                                sftp_server_info["password"],
                                sftp_server_info["sftp_filepath"],
                                sftp_server_info["local_filepath"],
                                sftp_server_info["local_filepath_archive"],
                                fname,
                            )
            except OSError as e:
                print("Failed upload .CSV files to remote. Error: ", str(e))
                set_option(mysqlcon, "upload_csv_sftp", False, time1)

            print("#919 - Finished \o/")
            set_option(mysqlcon, "upload_csv_sftp", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "upload_csv_sftp", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s" % datetime.datetime.now())
