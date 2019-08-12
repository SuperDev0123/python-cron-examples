# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
from pydash import _

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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


def get_dme_numbers(csv_lines):
    dme_numbers = []

    for i, csv_line in enumerate(csv_lines):
        if i % 5000 == 0 and IS_DEBUG:
            print("#", i)

        label_code = csv_line.split(",")[0]
        dme_number = label_code[3:-3]

        if dme_number not in dme_numbers:
            dme_numbers.append(dme_number)

    return dme_numbers


def get_api_bcl(label_code, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `fk_booking_id`, `fk_booking_line_id`, `fp_event_date`, `tally` \
                FROM `api_booking_confirmation_lines` \
                WHERE `label_code`=%s"
        cursor.execute(sql, (label_code))
        result = cursor.fetchone()
        return result


def get_booking(dme_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_booking_id`, `e_qty_scanned_fp_total` \
                From `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (dme_number))
        booking = cursor.fetchone()

        return booking


def get_booking_lines(pk_booking_id, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pk_lines_id`, `client_item_reference` \
                From `dme_booking_lines` \
                WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (pk_booking_id))
        booking_lines = cursor.fetchall()

        return booking_lines


def update_tally(api_bcl, mysqlcon):
    with mysqlcon.cursor() as cursor:
        tally = api_bcl["tally"]

        if not tally:
            tally = 0
            sql = "UPDATE `dme_bookings` \
                SET z_first_scan_label_date=%s \
                WHERE `pk_booking_id`=%s"
            cursor.execute(
                sql, (datetime.datetime.now().date(), api_bcl["fk_booking_id"])
            )
            mysqlcon.commit()

        sql = "UPDATE `api_booking_confirmation_lines` \
                SET tally=%s \
                WHERE `id`=%s"
        cursor.execute(sql, (int(tally) + 1, api_bcl["id"]))
        mysqlcon.commit()


def update_api_bcl(api_bcl, fp_event_date, fp_event_time, fp_scan_data, mysqlcon):
    with mysqlcon.cursor() as cursor:
        tally = api_bcl["tally"]

        if not tally:
            tally = 0
            sql = "UPDATE `dme_bookings` \
                SET z_first_scan_label_date=%s \
                WHERE `pk_booking_id`=%s"
            cursor.execute(
                sql, (datetime.datetime.now().date(), api_bcl["fk_booking_id"])
            )
            mysqlcon.commit()

        sql = "UPDATE `api_booking_confirmation_lines` \
                SET fp_event_date=%s, fp_event_time=%s, fp_scan_data=%s, tally=%s \
                WHERE `id`=%s"
        cursor.execute(
            sql,
            (fp_event_date, fp_event_time, fp_scan_data, int(tally) + 1, api_bcl["id"]),
        )
        mysqlcon.commit()


def update_booking_line(booking_line, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `tally` \
            FROM api_booking_confirmation_lines \
            WHERE `fk_booking_line_id`=%s"
        cursor.execute(sql, (booking_line["pk_lines_id"]))
        api_bcls = cursor.fetchall()

        e_qty_scanned_fp = 0
        for api_bcl in api_bcls:
            if api_bcl["tally"] is not None and int(api_bcl["tally"]) > 0:
                e_qty_scanned_fp += 1

        sql = "UPDATE `dme_booking_lines` \
            SET `e_qty_scanned_fp`=%s \
            WHERE `pk_lines_id`=%s"
        cursor.execute(sql, (e_qty_scanned_fp, booking_line["pk_lines_id"]))
        mysqlcon.commit()


def update_booking(booking, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `tally` \
            FROM api_booking_confirmation_lines \
            WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (booking["pk_booking_id"]))
        api_bcls = cursor.fetchall()

        e_qty_scanned_fp_total = 0
        for api_bcl in api_bcls:
            if api_bcl["tally"] is not None and int(api_bcl["tally"]) > 0:
                e_qty_scanned_fp_total += 1

        if (
            not booking["e_qty_scanned_fp_total"]
            or booking["e_qty_scanned_fp_total"] == "0"
        ):
            sql = "UPDATE `dme_bookings` \
                SET `b_status_API`=%s, `e_qty_scanned_fp_total`=%s \
                WHERE `id`=%s"
            cursor.execute(
                sql, ("update status", e_qty_scanned_fp_total, booking["id"])
            )
            mysqlcon.commit()
        else:
            sql = "UPDATE `dme_bookings` \
                SET `e_qty_scanned_fp_total`=%s \
                WHERE `id`=%s"
            cursor.execute(sql, (e_qty_scanned_fp_total, booking["id"]))
            mysqlcon.commit()


def do_calc_scanned(dme_number, dme_number_lines, mysqlcon):
    booking = get_booking(dme_number, mysqlcon)

    if not booking:
        return

    booking_lines = get_booking_lines(booking["pk_booking_id"], mysqlcon)

    if IS_DEBUG:
        print(
            "@802 - v_FPBookingNumber:", dme_number, " Lines cnt:", len(booking_lines)
        )

    scanned_label_codes = []
    for booking_line in booking_lines:
        for dme_number_line in dme_number_lines:
            label_code = dme_number_line["label_code"]
            client_item_reference = dme_number_line["client_item_reference"]
            api_bcl = get_api_bcl(label_code, mysqlcon)

            if not api_bcl:
                continue

            if int(booking_line["pk_lines_id"]) == int(api_bcl["fk_booking_line_id"]):
                if label_code in scanned_label_codes:
                    update_tally(api_bcl, mysqlcon)
                else:
                    scanned_label_codes.append(label_code)
                    update_api_bcl(
                        api_bcl,
                        dme_number_line["date"],
                        dme_number_line["time"],
                        dme_number_line["scanned_by"],
                        mysqlcon,
                    )

        update_booking_line(booking_line, mysqlcon)
    update_booking(booking, mysqlcon)


def save_csv_into_db(dme_number_lines, mysqlcon):
    with mysqlcon.cursor() as cursor:
        for dme_number_line in dme_number_lines:
            sql = "INSERT INTO `fp_label_scans` \
                (`fk_fp`, `label_code`, `client_item_reference`, `scanned_date`, \
                 `scanned_time`, `scanned_by`, `z_createdTimeStamp`) \
                VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(
                sql,
                (
                    1,
                    dme_number_line["label_code"],
                    dme_number_line["client_item_reference"],
                    dme_number_line["date"],
                    dme_number_line["time"],
                    dme_number_line["scanned_by"],
                    datetime.datetime.now(),
                ),
            )
            mysqlcon.commit()


def do_process_one(dme_number, csv_lines, mysqlcon):
    # filter with `dme_number`
    dme_number_lines = _.filter_(
        csv_lines, lambda x: x.split(",")[0][3:-3] == dme_number
    )

    # string -> object
    dme_number_lines = _.map_(
        dme_number_lines,
        lambda x: {
            "label_code": x.split(",")[0],
            "client_item_reference": x.split(",")[1].split(" ")[-1],
            "date": datetime.datetime.strptime(x.split(",")[2], "%Y-%m-%d"),
            "time": datetime.datetime.strptime(x.split(",")[3] + ":00", "%H:%M:%S"),
            "scanned_by": x.split(",")[4].split(" ")[2][:-1],
        },
    )

    # sort by `label_code`(first field)
    dme_number_lines = _.sort_by(dme_number_lines, "label_code")

    # show
    if IS_DEBUG and False:
        _.map_(
            dme_number_lines,
            lambda x: print(
                f'{dme_number}({len(dme_number_lines)}) - {x["label_code"]}, {x["client_item_reference"]}'
            ),
        )

    save_csv_into_db(dme_number_lines, mysqlcon)
    do_calc_scanned(dme_number, dme_number_lines, mysqlcon)


def do_process(fpath, mysqlcon):
    csv_lines = []

    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            csv_lines.append(line)

        dme_numbers = get_dme_numbers(csv_lines)

        if not dme_numbers:
            return "Can not find dme numbers"
        else:
            for i, dme_number in enumerate(dme_numbers):
                if i % 100 == 0:
                    print(f"@888 {i}th DME number: {dme_number}")
                do_process_one(dme_number, csv_lines, mysqlcon)

    return f"Successfully processed({len(csv_lines)} lines)"


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

    if IS_PRODUCTION:
        CSV_DIR = "/home/cope_au/dme_sftp/cope_au/scans_labels/indata/"
        ARCHIVE_DIR = "/home/cope_au/dme_sftp/cope_au/scans_labels/archive/"
    else:
        CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
        ARCHIVE_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

    if not os.path.isdir(CSV_DIR):
        print('Given argument "%s" is not a directory' % CSV_DIR)
        exit(1)

    try:
        for fname in sorted(os.listdir(CSV_DIR)):
            fpath = os.path.join(CSV_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".csv"):
                print("@100 Detect csv file:", fpath)
                result = do_process(fpath, mysqlcon)
                print(f"#901 - Process result: {result}")
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print("@109 Moved csv file:", fpath)

    except OSError as e:
        print(str(e))

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
