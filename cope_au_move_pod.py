# Python 3.6.6

import sys, time
import os
import errno
import datetime
import pymysql, pymysql.cursors
import shutil
import glob
import ntpath

import _status_history

# env_mode = 0  # Local
# env_mode = 1  # Dev
env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"
elif env_mode == 1:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
elif env_mode == 2:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_prod"  # Prod


def get_filename(filename, visual_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pu_Address_State`, `b_client_sales_inv_num` FROM `dme_bookings` WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (visual_id))
        result = cursor.fetchone()
        if result is None:
            print("@102 - booking is not exist with this visual_id: ", visual_id)
            return None
        else:
            if (
                result["pu_Address_State"] is None
                or result["b_client_sales_inv_num"] is None
            ):
                print(
                    f"@102 - booking({visual_id}) does not have `pu_Address_State` or `b_client_sales_inv_num`"
                )
                return None
            else:
                if "POD_SOG_" in filename:
                    new_filename = (
                        "POD_SOG_"
                        + result["pu_Address_State"]
                        + "_"
                        + result["b_client_sales_inv_num"]
                        + "_"
                        + filename[8:]
                    )
                else:
                    new_filename = (
                        "POD_"
                        + result["pu_Address_State"]
                        + "_"
                        + result["b_client_sales_inv_num"]
                        + "_"
                        + filename
                    )
                return new_filename


def get_booking_with_visual_id(visual_id, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `z_lock_status`, `b_status`, `pk_booking_id`, `b_bookingID_Visual`, `tally_delivered` \
                FROM `dme_bookings` \
                WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (visual_id))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result


def calc_delivered(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        tally_delivered = booking["tally_delivered"]

        if not tally_delivered:
            tally_delivered = 0

        sql = "UPDATE `dme_bookings` \
                SET `tally_delivered`=%s \
                WHERE `id`=%s"
        cursor.execute(sql, (int(tally_delivered) + 1, booking["id"]))
        mysqlcon.commit()

        sql = "SELECT `pk_lines_id`, `e_qty`, `e_qty_awaiting_inventory`, `e_qty_delivered` \
                FROM `dme_booking_lines` \
                WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (booking["pk_booking_id"]))
        booking_lines = cursor.fetchall()

        for booking_line in booking_lines:
            if not booking_line["e_qty"]:
                booking_line["e_qty"] = 0
            if not booking_line["e_qty_awaiting_inventory"]:
                booking_line["e_qty_awaiting_inventory"] = 0

            booking_line["e_qty_delivered"] = int(booking_line["e_qty"]) - int(
                booking_line["e_qty_awaiting_inventory"]
            )

            sql = "UPDATE `dme_booking_lines` \
                    SET `e_qty_delivered`=%s \
                    WHERE `pk_lines_id`=%s"
            cursor.execute(
                sql, (booking_line["e_qty_delivered"], booking_line["pk_lines_id"])
            )
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

    if env_mode == 0:
        source_url = "/Users/admin/work/goldmine/scripts/dir01/"
        dest_url_0 = "/Users/admin/work/goldmine/scripts/dir02/"
        dest_url_1 = dest_url_0
        dup_url = "/Users/admin/work/goldmine/scripts/dir_dups/"
    else:
        source_url = "/home/cope_au/dme_sftp/cope_au/pods/indata/"
        dest_url_0 = "/home/cope_au/dme_sftp/cope_au/pods/archive/"
        dest_url_1 = "/opt/s3_public/imgs/"
        dup_url = "/home/cope_au/dme_sftp/cope_au/pods/duplicates/"

    LIMIT = 50
    count = 0
    for file in os.listdir(source_url):
        count += 1
        if count > LIMIT:
            break

        filename = ntpath.basename(file)

        if not "DS_Store" in filename:
            if "POD_SOG_" in filename:
                subname = filename[8:]
                if "_" in subname:
                    visual_id = int(subname.split("_")[1].split(".")[0])
                else:
                    visual_id = int(subname[3:].split(".")[0])
            else:
                if "_" in filename:
                    visual_id = int(filename.split("_")[1].split(".")[0])
                else:
                    visual_id = int(filename[3:].split(".")[0])

            new_filename = get_filename(filename, visual_id)

            if new_filename is not None:
                print(
                    "@100 - File name: ",
                    filename,
                    "Visual ID: ",
                    visual_id,
                    "New name:",
                    new_filename,
                )

                if new_filename:
                    exists = os.path.isfile(dest_url_0 + new_filename)
                    booking = get_booking_with_visual_id(visual_id, mysqlcon)

                    if exists:
                        try:
                            shutil.copy(
                                source_url + filename, dest_url_0 + new_filename
                            )
                            shutil.move(
                                source_url + filename, dest_url_1 + new_filename
                            )

                            with mysqlcon.cursor() as cursor:
                                if "POD_SOG_" in filename:
                                    sql = "UPDATE `dme_bookings` set z_downloaded_pod_sog_timestamp=%s WHERE `b_bookingID_Visual`=%s"
                                    cursor.execute(sql, (None, visual_id))
                                else:
                                    sql = "UPDATE `dme_bookings` set z_downloaded_pod_timestamp=%s WHERE `b_bookingID_Visual`=%s"
                                    cursor.execute(sql, (None, visual_id))
                            mysqlcon.commit()
                        except IOError as e:
                            print("#108 Unable to copy or move file. %s" % e)
                    else:
                        try:
                            shutil.copy(
                                source_url + filename, dest_url_0 + new_filename
                            )
                            shutil.move(
                                source_url + filename, dest_url_1 + new_filename
                            )

                            with mysqlcon.cursor() as cursor:
                                if booking["z_lock_status"] == 1:
                                    if "POD_SOG_" in filename:
                                        sql = "UPDATE `dme_bookings` \
                                                SET `z_pod_signed_url`=%s, z_status_process_notes=%s, \
                                                rpt_pod_from_file_time=%s, z_downloaded_pod_sog_timestamp=%s \
                                                WHERE `b_bookingID_Visual`=%s"
                                    else:
                                        sql = "UPDATE `dme_bookings` \
                                                SET `z_pod_url`=%s, z_status_process_notes=%s, \
                                                rpt_pod_from_file_time=%s, z_downloaded_pod_sog_timestamp=%s \
                                                WHERE `b_bookingID_Visual`=%s"

                                    cursor.execute(
                                        sql,
                                        (
                                            new_filename,
                                            "Status was locked with ("
                                            + booking["b_status"]
                                            + ") - POD Received not set",
                                            datetime.datetime.now(),
                                            None,
                                            visual_id,
                                        ),
                                    )
                                    mysqlcon.commit()
                                    _status_history.create(
                                        booking["id"],
                                        None,
                                        datetime.datetime.now(),
                                        "Delivered",
                                    )
                                else:
                                    if "POD_SOG_" in filename:
                                        sql = "UPDATE `dme_bookings` \
                                                SET `z_pod_signed_url`=%s, b_status=%s, b_status_API=%s, \
                                                rpt_pod_from_file_time=%s, z_downloaded_pod_sog_timestamp=%s \
                                                WHERE `b_bookingID_Visual`=%s"
                                    else:
                                        sql = "UPDATE `dme_bookings` \
                                                SET `z_pod_url`=%s, b_status=%s, b_status_API=%s, \
                                                rpt_pod_from_file_time=%s, z_downloaded_pod_timestamp=%s \
                                                WHERE `b_bookingID_Visual`=%s"
                                    cursor.execute(
                                        sql,
                                        (
                                            new_filename,
                                            "Delivered",
                                            "POD Received",
                                            datetime.datetime.now(),
                                            None,
                                            visual_id,
                                        ),
                                    )
                                    mysqlcon.commit()

                                    _status_history.create(
                                        booking["id"],
                                        None,
                                        datetime.datetime.now(),
                                        "Delivered",
                                    )
                                    calc_delivered(booking, mysqlcon)
                        except IOError as e:
                            print("#104 Unable to copy or move file. %s" % e)

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
