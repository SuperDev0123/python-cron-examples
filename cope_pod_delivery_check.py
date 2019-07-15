# Python 3.6.6

import sys, time
import os
import io
import errno
import uuid
import json
import base64
import shutil
import datetime
import zipfile
import pymysql, pymysql.cursors

# production = True  # Dev
production = False  # Local

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
    ZIP_DIR = "/home/cope_au/dme_sftp/cope_au/weekly_pod_zips/"
    SRC_DIR = "/var/www/html/dme_api/static/imgs/"
else:
    ZIP_DIR = "/Users/admin/work/goldmine/scripts/dir02/"
    SRC_DIR = "/Users/admin/work/goldmine/dme_api/static/imgs/"


def clear_download_timestamp(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE dme_bookings \
                SET z_downloaded_pod_timestamp=null, z_downloaded_pod_sog_timestamp=null, z_ModifiedTimestamp=%s \
                WHERE vx_freight_provider=%s and z_CreatedTimestamp=%s"
        cursor.execute(sql, ("Cope", datetime.datetime.now(), "2019-07-13 00:00:00"))
        mysqlcon.commit()


def zip_weekly(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, z_pod_url, z_pod_signed_url, z_CreatedTimestamp, s_21_ActualDeliveryTimeStamp, b_bookingID_Visual \
                FROM `dme_bookings` \
                WHERE vx_freight_provider=%s \
                    and z_CreatedTimestamp=%s \
                    and s_21_ActualDeliveryTimeStamp is not null \
                    and ( \
                        (z_pod_url <> '' and z_pod_url is not null) \
                        or (z_pod_signed_url <> '' and z_pod_signed_url is not null) \
                    ) \
                ORDER BY s_21_ActualDeliveryTimeStamp"
        cursor.execute(sql, ("Cope", "2019-07-13 00:00:00"))
        bookings = cursor.fetchall()

        # Separate into each week
        weeks = {}
        for booking in bookings:
            year = booking["s_21_ActualDeliveryTimeStamp"].year
            month = booking["s_21_ActualDeliveryTimeStamp"].month
            day = booking["s_21_ActualDeliveryTimeStamp"].day
            week_info = datetime.datetime(year, month, day).isocalendar()
            week_start_date = datetime.datetime.strptime(
                str(week_info[0]) + "-" + str(week_info[1] - 1) + "-1", "%Y-%W-%w"
            )
            week_end_date = week_start_date + datetime.timedelta(days=6)

            key = f"{week_start_date.date()}__{week_end_date.date()}"
            if not key in weeks:
                weeks[key] = [
                    {
                        "z_pod_url": booking["z_pod_url"],
                        "z_pod_signed_url": booking["z_pod_signed_url"],
                        "id": booking["id"],
                        "b_bookingID_Visual": booking["b_bookingID_Visual"],
                    }
                ]
            else:
                weeks[key].append(
                    {
                        "z_pod_url": booking["z_pod_url"],
                        "z_pod_signed_url": booking["z_pod_signed_url"],
                        "id": booking["id"],
                        "b_bookingID_Visual": booking["b_bookingID_Visual"],
                    }
                )

        # Build zip files
        for key in weeks:
            file_paths = []
            filenames = []
            bookings_cnt = 0

            for booking in weeks[key]:
                if booking["z_pod_url"] or booking["z_pod_signed_url"]:
                    bookings_cnt += 1

                if booking["z_pod_url"]:
                    if os.path.exists(SRC_DIR + booking["z_pod_url"]):
                        file_paths.append(SRC_DIR + booking["z_pod_url"])
                        filenames.append(booking["z_pod_url"])
                    else:
                        sql = "UPDATE dme_bookings \
                                SET b_error_Capture=%s, z_ModifiedTimestamp=%s \
                                WHERE id=%s"
                        cursor.execute(
                            sql,
                            (
                                "POD or POD_SOG is missing",
                                datetime.datetime.now(),
                                booking["id"],
                            ),
                        )
                        mysqlcon.commit()
                        print("#925 Missing POD: ", booking["b_bookingID_Visual"])

                if booking["z_pod_signed_url"]:
                    if os.path.exists(SRC_DIR + booking["z_pod_signed_url"]):
                        file_paths.append(SRC_DIR + booking["z_pod_signed_url"])
                        filenames.append(booking["z_pod_signed_url"])
                    else:
                        sql = "UPDATE dme_bookings \
                                SET b_error_Capture=%s, z_ModifiedTimestamp=%s \
                                WHERE id=%s"
                        cursor.execute(
                            sql,
                            (
                                "POD or POD_SOG is missing",
                                datetime.datetime.now(),
                                booking["id"],
                            ),
                        )
                        mysqlcon.commit()
                        print("#925 Missing POD_SOG: ", booking["b_bookingID_Visual"])

            zip_subdir = ZIP_DIR + key + "__" + str(bookings_cnt)
            zip_filename = f"{zip_subdir}.zip"
            zf = zipfile.ZipFile(zip_filename, "w")

            for index, file_path in enumerate(file_paths):
                zip_path = os.path.join(zip_subdir, file_path)
                zf.write(file_path, filenames[index])

            zf.close()

        # Update download timestamp
        for key in weeks:
            for booking in weeks[key]:
                if booking["z_pod_url"] and os.path.exists(
                    SRC_DIR + booking["z_pod_url"]
                ):
                    sql = "UPDATE dme_bookings \
                            SET z_downloaded_pod_timestamp=%s \
                            WHERE id=%s"
                    cursor.execute(sql, (datetime.datetime.now(), booking["id"]))
                    mysqlcon.commit()

                if booking["z_pod_signed_url"] and os.path.exists(
                    SRC_DIR + booking["z_pod_signed_url"]
                ):
                    sql = "UPDATE dme_bookings \
                            SET z_downloaded_pod_sog_timestamp=%s \
                            WHERE id=%s"
                    cursor.execute(sql, (datetime.datetime.now(), booking["id"]))
                    mysqlcon.commit()


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
        clear_download_timestamp(mysqlcon)
        print("#920 Sucess: Clear download timestamp")
    except OSError as e:
        print("#902 Error", str(e))

    try:
        zip_weekly(mysqlcon)
        print("#920 Sucess: Build weekly zips")
    except OSError as e:
        print("#903 Error", str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
