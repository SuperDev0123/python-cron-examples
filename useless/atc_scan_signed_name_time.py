# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import pysftp
import json

IS_DEBUG = False
# IS_PRODUCTION = True  # Dev
IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = 'dme_db_dev'  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    JSON_DIR = "/home/cope_au/dme_sftp/atc_au/ftp/indata/"
    ARCHIVE_JSON_DIR = "/home/cope_au/dme_sftp/atc_au/ftp/archive/"
    CSV_DIR = "/home/cope_au/dme_sftp/atc_au/pickup_ext/indata/"
    ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/atc_au/pickup_ext/archive/"
else:
    JSON_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
    ARCHIVE_JSON_DIR = "/Users/admin/work/goldmine/scripts/dir02/"
    CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
    ARCHIVE_CSV_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

# sftp server infos
sftp_server_infos = {
    "atc": {
        "type": "Freight Provider",
        "name": "ATC",
        "host": "batchprocessing.hubsystems.com.au",
        "username": "atc-biopak2",
        "password": "SWojmGeLLFm",
        "sftp_filepath": "/track/",
        "local_filepath": JSON_DIR,
        "local_filepath_archive": ARCHIVE_JSON_DIR,
    },
    "biopak": {
        "type": "Client",
        "name": "BIOPAK",
        "host": "ftp.biopak.com.au",
        "username": "dme_biopak",
        "password": "3rp2NcHS",
        "sftp_filepath": "/DME/POD/",
        "local_filepath": CSV_DIR,
        "local_filepath_archive": ARCHIVE_CSV_DIR,
    },
}


def download_sftp(
    host, username, password, sftp_filepath, local_filepath, local_filepath_archive
):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host=host, username=username, password=password, cnopts=cnopts
    ) as sftp_con:
        print("@102 - Connected to sftp")

        with sftp_con.cd(sftp_filepath):
            print("@103 - Go to sftp dir")

            for file in sftp_con.listdir():
                lstatout = str(sftp_con.lstat(file)).split()[0]

                if "d" not in lstatout and file.endswith(".json"):  # If file
                    print("@104 - Downloading: ", file)
                    sftp_con.get(sftp_filepath + file, local_filepath + file)
                    sftp_file_size = sftp_con.lstat(sftp_filepath + file).st_size
                    local_file_size = os.stat(local_filepath + file).st_size

                    if sftp_file_size == local_file_size:  # Check file size
                        print("@105 - Move: " + file)
                        sftp_con.rename(
                            sftp_filepath + file, "/archive/" + file
                        )  # Move file to `archive`

        sftp_con.close()


def csv_write(fpath, f, mysqlcon):
    # Write Header
    f.write("consignment_number, date_of_delivery, status, pod_name, reason")
    with mysqlcon.cursor() as cursor:
        json_file = open(fpath, "r")
        json_content = json.loads(json_file.read())

        consignment_number = json_content["consignment"]
        booking = get_booking(consignment_number, mysqlcon)

        if booking:
            b_del_to_signed_time = datetime.datetime.strptime(
                json_content["eventdatetime"], "%Y%m%dT%H%M%S"
            )
            b_del_to_signed_name = json_content["podname"]
            type_flag = json_content["status"]

            print(
                "@200 - ",
                consignment_number,
                b_del_to_signed_time,
                b_del_to_signed_name,
                type_flag,
            )

            sql = "UPDATE `dme_bookings` \
                SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s \
                WHERE `v_FPBookingNumber`=%s"
            cursor.execute(
                sql,
                (
                    b_del_to_signed_name,
                    b_del_to_signed_time,
                    datetime.datetime.now(),
                    type_flag_transit_state[type_flag],
                    consignment_number,
                ),
            )
            mysqlcon.commit()

            # Write Each Line
            comma = ","
            newLine = "\n"
            eachLineText = consignment_number + comma
            eachLineText += b_del_to_signed_time.strftime("%Y%m%d") + comma
            eachLineText += type_flag + comma
            eachLineText += b_del_to_signed_name + comma

            f.write(newLine + eachLineText)
        else:
            print("@400: Booking not found - ", consignment_number)


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

    if not os.path.isdir(JSON_DIR) or not os.path.isdir(CSV_DIR):
        print('Given argument "%s, %s" is not a directory' % JSON_DIR, CSV_DIR)
        exit(1)

    # Download .json files
    try:
        download_sftp(
            sftp_server_infos["atc"]["host"],
            sftp_server_infos["atc"]["username"],
            sftp_server_infos["atc"]["password"],
            sftp_server_infos["atc"]["sftp_filepath"],
            sftp_server_infos["atc"]["local_filepath"],
            sftp_server_infos["atc"]["local_filepath_archive"],
        )
    except OSError as e:
        print("Failed download .json files from remote. Error: ", str(e))

    try:
        for fname in sorted(os.listdir(JSON_DIR)):
            fpath = os.path.join(JSON_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".json"):
                print("@100 Detect .json file:", fpath)

                csv_name = (
                    str(datetime.datetime.now().strftime("%d-%m-%Y__%H_%M_%S")) + ".csv"
                )
                f = open(CSV_DIR + csv_name, "w+")
                csv_write(fpath, f, mysqlcon)
                f.close()

                upload_sftp(
                    sftp_server_infos["biopak"]["host"],
                    sftp_server_infos["biopak"]["username"],
                    sftp_server_infos["biopak"]["password"],
                    sftp_server_infos["biopak"]["sftp_filepath"],
                    sftp_server_infos["biopak"]["local_filepath"],
                    sftp_server_infos["biopak"]["local_filepath_archive"],
                    csv_name,
                )

                shutil.move(JSON_DIR + fname, ARCHIVE_JSON_DIR + fname)
                print("@109 Moved .json file:", fpath)

    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
