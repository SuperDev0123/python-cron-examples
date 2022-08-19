# Python 3.7.0
# V 2.0
import os, sys, time, json
import pymysql, pymysql.cursors
import datetime
import shutil
import glob
import ntpath

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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


def get_booking(b_bookingID_Visual, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, b_bookingID_Visual, pk_booking_id, b_client_sales_inv_num \
                FROM `dme_bookings` \
                WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (b_bookingID_Visual))
        booking = cursor.fetchone()

        return booking


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

    source_url = "/home/cope_au/dme_sftp/cope_au/pod_reruns/"
    dest_url = "/home/cope_au/dme_sftp/cope_au/pod_reruns_with_sinv/"

    try:
        for file in os.listdir(source_url):
            filename = ntpath.basename(file)

            if "POD_SOG_" in filename:
                b_bookingID_Visual = filename[8:]
                b_bookingID_Visual = b_bookingID_Visual[:-4]
                b_bookingID_Visual = b_bookingID_Visual[4:]
                print("@200 - ", b_bookingID_Visual)
                booking = get_booking(b_bookingID_Visual, mysqlcon)

                if booking:
                    new_filename = (
                        f"{filename[:-4]}_{booking['b_client_sales_inv_num']}.pdf"
                    )
                    print(f"@200=1 - {filename} -> {new_filename}")
                    shutil.move(source_url + filename, dest_url + new_filename)

    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
