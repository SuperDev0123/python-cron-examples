# Python 3.6.6

import os, sys
import datetime
import shutil
import pysftp
import pymysql, pymysql.cursors

IS_DEBUG = False
IS_PRODUCTION = True  # Dev

if IS_PRODUCTION:
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

# CSV sftp server info
sftp_server_infos = [
    {
        "fp_name": "Cope",
        "host": "esmart.cope.com.au",
        "username": "deliverme",
        "password": "C3n?7u4f",
        "sftp_filepath": "/home/import/csvimport/upload/",
        "local_filepath": "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/",
        "local_filepath_dup": "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/archive/",
    },
    {
        # DHL QA(test) server info
        "fp_name": "DHL",
        "host": "ftp2-dhllink-qa.dhl.com",
        "username": "deliverme_au_tst_sftp",
        "password": "Rbk3Zxi605_5YCIU",
        "sftp_filepath": "/in/",
        "local_filepath": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/",
        "local_filepath_dup": "/home/cope_au/dme_sftp/cope_au/pickup_ext/dhl_au/archive/",
    },
]


def upload_sftp(
    host,
    username,
    password,
    sftp_filepath,
    local_filepath,
    local_filepath_dup,
    filename,
):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host=host, username=username, password=password, cnopts=cnopts
    ) as sftp_con:
        print("@102 - Connected to sftp")
        with sftp_con.cd(sftp_filepath):
            print("@103 - Go to sftp dir")
            sftp_con.put(local_filepath + filename)
            sftp_file_size = sftp_con.lstat(sftp_filepath + filename).st_size
            local_file_size = os.stat(local_filepath + filename).st_size

            if sftp_file_size == local_file_size:
                if not os.path.exists(local_filepath_dup):
                    os.makedirs(local_filepath_dup)
                shutil.move(local_filepath + filename, local_filepath_dup + filename)
                print("@109 Moved csv file:", filename)

        sftp_con.close()


def can_run(fp_name, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_options` \
                WHERE option_name=%s"
        cursor.execute(sql, ("upload_csv_sftp_" + fp_name.lower()))
        result = cursor.fetchone()

        if int(result["option_value"]):
            return True
        return False


if __name__ == "__main__":
    print("#900 - Started at %s" % datetime.datetime.now())

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
        fp_name = sys.argv[1]

        for sftp_server_info in sftp_server_infos:
            if fp_name == sftp_server_info["fp_name"]:
                if not can_run(fp_name, mysqlcon):
                    print(f"#901 - Script has been deactivated for `{fp_name}`")
                else:
                    print(f"#901 - Running for `{fp_name}`")

                    for fname in os.listdir(sftp_server_info["local_filepath"]):
                        fpath = os.path.join(sftp_server_info["local_filepath"], fname)

                        if os.path.isfile(fpath) and fname.endswith(".csv"):
                            print("@100 Detect csv file:", fpath)
                            upload_sftp(
                                sftp_server_info["host"],
                                sftp_server_info["username"],
                                sftp_server_info["password"],
                                sftp_server_info["sftp_filepath"],
                                sftp_server_info["local_filepath"],
                                sftp_server_info["local_filepath_dup"],
                                fname,
                            )
    except OSError as e:
        print(str(e))

    print("#999 - Finished at %s" % datetime.datetime.now())
