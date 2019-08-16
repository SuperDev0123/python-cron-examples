# Python 3.6.6

import sys, time
import os
import io
import json
import shutil
import datetime
import zipfile
import pymysql, pymysql.cursors

production = True  # Dev
# production = False  # Local

if production:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = "dme_db_dev"  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if production:
    ZIP_DIR = "/opt/s3_privates/daily_new_pods/"
    SRC_DIR = "/opt/s3_public/pdfs/cope_au/"
else:
    ZIP_DIR = "/Users/admin/work/goldmine/scripts/dir02/"
    SRC_DIR = "/Users/admin/work/goldmine/dme_api/static/pdfs/"


def get_available_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, z_pod_url, z_pod_signed_url, z_downloaded_pod_timestamp, z_downloaded_pod_sog_timestamp \
                FROM dme_bookings \
                WHERE (z_pod_url is not null and z_pod_url != '' and z_downloaded_pod_timestamp is null) \
                or (z_pod_signed_url is not null and z_pod_signed_url != '' and z_downloaded_pod_sog_timestamp is null)"
        cursor.execute(sql)
        bookings = cursor.fetchall()
        return bookings


def update_download_status(bookings, mysqlcon):
    with mysqlcon.cursor() as cursor:
        for booking in bookings:
            if (
                booking["z_pod_url"] is not None
                and booking["z_pod_url"] != ""
                and not booking["z_downloaded_pod_timestamp"]
            ):
                sql = "UPDATE dme_bookings \
                        SET z_downloaded_pod_timestamp=%s \
                        WHERE id=%s"
                cursor.execute(sql, (datetime.datetime.now(), booking["id"]))
                mysqlcon.commit()

            if (
                booking["z_pod_signed_url"] is not None
                and booking["z_pod_signed_url"] != ""
                and not booking["z_downloaded_pod_sog_timestamp"]
            ):
                sql = "UPDATE dme_bookings \
                        SET z_downloaded_pod_sog_timestamp=%s \
                        WHERE id=%s"
                cursor.execute(sql, (datetime.datetime.now(), booking["id"]))
                mysqlcon.commit()


def zip_new_pods(mysqlcon):
    bookings = get_available_bookings(mysqlcon)

    if len(bookings) > 0:
        file_paths = []
        filenames = []

        for booking in bookings:
            if (
                booking["z_pod_url"] is not None
                and booking["z_pod_url"] != ""
                and not booking["z_downloaded_pod_timestamp"]
            ):
                file_paths.append(SRC_DIR + booking["z_pod_url"])
                filenames.append(booking["z_pod_url"])

            if (
                booking["z_pod_signed_url"] is not None
                and booking["z_pod_signed_url"] != ""
                and not booking["z_downloaded_pod_sog_timestamp"]
            ):
                file_paths.append(SRC_DIR + booking["z_pod_signed_url"])
                filenames.append(booking["z_pod_signed_url"])

        zip_subdir = (
            ZIP_DIR
            + str(datetime.datetime.now().strftime("%Y-%m-%d"))
            + "__"
            + str(len(file_paths))
        )
        zip_filename = f"{zip_subdir}.zip"
        zf = zipfile.ZipFile(zip_filename, "w")

        for index, file_path in enumerate(file_paths):
            zip_path = os.path.join(zip_subdir, file_path)
            zf.write(file_path, filenames[index])

        zf.close()

        update_download_status(bookings, mysqlcon)


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

    try:
        zip_new_pods(mysqlcon)
        print("#920 Sucess: zip new pods")
    except OSError as e:
        print("#902 Error", str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
