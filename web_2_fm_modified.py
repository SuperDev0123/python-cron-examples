# Python 3.6.6
# V 1.0
import os, sys, time, json
from datetime import datetime
import pymysql, pymysql.cursors
import xlsxwriter as xlsxwriter

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME
from _sharepoint_lib import Office365, Site
from _datetime_lib import convert_to_AU_SYDNEY_tz
from _options_lib import get_option, set_option


def get_begin_timestamp(option):
    if option and "arg2" in option:
        return option["arg2"]


def _trun_off_flag(mysqlcon, flag_name):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_options` \
                SET option_value=%s \
                WHERE option_name=%s"
        cursor.execute(sql, (0, flag_name))
        mysqlcon.commit()


def get_bookings(mysqlcon, begin_ts):
    # Get bookings which modified after begin_ts and then delta(z_ModifiedTimestamp, z_CreatedTimestamp) is over 5 min
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_bookings` \
                WHERE z_ModifiedTimestamp>%s and z_ModifiedTimestamp - z_CreatedTimestamp>%s \
                    and b_client_name<>%s \
                ORDER BY id"
        cursor.execute(sql, (begin_ts, 300, "BioPak"))
        results = cursor.fetchall()
        return results


def get_booking_lines(mysqlcon, pk_booking_ids):
    with mysqlcon.cursor() as cursor:
        sql = f"SELECT * FROM `dme_booking_lines` WHERE fk_booking_id in ({','.join(pk_booking_ids)}) ORDER BY pk_lines_id"
        cursor.execute(sql)
        results = cursor.fetchall()
        return results


def get_booking_line_datas(mysqlcon, pk_booking_ids):
    with mysqlcon.cursor() as cursor:
        sql = f"SELECT * FROM `dme_booking_lines_data` WHERE fk_booking_id in ({','.join(pk_booking_ids)}) ORDER BY pk_id_lines_data"
        cursor.execute(sql)
        results = cursor.fetchall()
        return results


def get_fields_info(mysqlcon, table_name):
    with mysqlcon.cursor() as cursor:
        sql = f"SHOW COLUMNS FROM {table_name}"
        cursor.execute(sql)
        results = cursor.fetchall()
        return results


def update_modified_timestamp(mysqlcon, pk_booking_ids):
    with mysqlcon.cursor() as cursor:
        now_timestamp = str(datetime.now())[:19]

        # Update dme_bookings
        sql = f"UPDATE dme_bookings SET z_ModifiedTimestamp=%s WHERE pk_booking_id in ({','.join(pk_booking_ids)})"
        cursor.execute(sql, (now_timestamp))

        # Update dme_booking_lines
        sql = f"UPDATE dme_booking_lines SET z_modifiedTimeStamp=%s WHERE fk_booking_id in ({','.join(pk_booking_ids)})"
        cursor.execute(sql, (now_timestamp))

        # Update dme_booking_lines_data
        sql = f"UPDATE dme_booking_lines_data SET z_modifiedTimeStamp=%s WHERE fk_booking_id in ({','.join(pk_booking_ids)})"
        cursor.execute(sql, (now_timestamp))

        mysqlcon.commit()


def upload_file_to_sharepoint(file_path, file_name):
    share_point_site = "https://delivermeee.sharepoint.com"
    username = "goldj@deliver-me.com.au"
    password = "qos131QOS131*"
    site_url = "https://delivermeee.sharepoint.com/sites/DeliverMECustomerSite/"
    folderpath = "Shared Documents/Bookings/Tempo/6_DME_Web_to_FM"

    authcookie = Office365(
        share_point_site=share_point_site, username=username, password=password
    ).get_cookies()
    site = Site(site_url=site_url, authcookie=authcookie)

    result = site.upload_file(
        folderpath=folderpath, filepath=file_path, filename=file_name
    )

    return result


def write_worksheet(name, workbook, worksheet, table, fields_info):
    worksheet.set_column(0, 200, width=25)
    bold = workbook.add_format({"bold": 1, "align": "left"})
    datetime_format = workbook.add_format({"num_format": "dd/mm/yyyy hh:mm:ss"})
    date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
    time_format = workbook.add_format({"num_format": "hh:mm:ss"})

    # Write header(field names)
    for col_index, field_info in enumerate(fields_info):
        worksheet.write(0, col_index, field_info["Field"], bold)

    # Write content
    for row_index, record in enumerate(table):
        if row_index % 10 == 0:
            print(f"@810 Building {name} worksheet... {row_index}/{len(table)}")

        col_index = 0
        for key in record:
            if record[key]:
                if "datetime" in fields_info[col_index]["Type"]:
                    worksheet.write(
                        row_index + 1, col_index, record[key], datetime_format
                    )
                elif "date" in fields_info[col_index]["Type"]:
                    worksheet.write(row_index + 1, col_index, record[key], date_format)
                elif "time" in fields_info[col_index]["Type"]:
                    worksheet.write(row_index + 1, col_index, record[key], time_format)
                else:
                    worksheet.write(row_index + 1, col_index, record[key])

            col_index += 1


def do_process(mysqlcon, option):
    # Get begin timestamp - arg2 field of dme_options table
    begin_ts = get_begin_timestamp(option)

    if not begin_ts:
        print(
            "#400 DB is not ready for this process(dme_options table has no `arg2` field)"
        )

    # Query DB
    print("#800 Quering DB...")
    bookings = get_bookings(mysqlcon, begin_ts)
    booking_fields_info = get_fields_info(mysqlcon, "dme_bookings")
    print(f"#801 - Begin timestamp: {begin_ts} Bookings cnt: {len(bookings)}")

    if not bookings:
        return True

    pk_booking_ids = []
    for booking in bookings:
        pk_booking_ids.append('"' + booking["pk_booking_id"] + '"')

    booking_lines = get_booking_lines(mysqlcon, pk_booking_ids)
    booking_lines_fields_info = get_fields_info(mysqlcon, "dme_booking_lines")
    print("#802 - Booking Lines cnt:", len(booking_lines))

    booking_line_datas = get_booking_line_datas(mysqlcon, pk_booking_ids)
    booking_line_datas_fields_info = get_fields_info(mysqlcon, "dme_booking_lines_data")
    print("#803 - Booking Lines Data cnt:", len(booking_line_datas))

    # File name
    local_filepath = "./temp_files/web_2_fm_modified"

    if not os.path.exists(local_filepath):
        os.makedirs(local_filepath)

    file_name = f'modified_{len(bookings)}_gte_{bookings[0]["b_bookingID_Visual"]}_{convert_to_AU_SYDNEY_tz(datetime.now()).strftime("%d-%m-%Y %H_%M_%S")}.xlsx'
    file_path = f"{local_filepath}/{file_name}"

    # Create workbook and worksheets
    workbook = xlsxwriter.Workbook(file_path, {"remove_timezone": True})
    worksheet_0 = workbook.add_worksheet("Bookings")
    worksheet_1 = workbook.add_worksheet("Booking Lines")
    worksheet_2 = workbook.add_worksheet("Booking Lines Data")

    # Write each worksheets
    print("#805 Building sheet...")
    write_worksheet("Bookings", workbook, worksheet_0, bookings, booking_fields_info)
    write_worksheet(
        "Booking Lines", workbook, worksheet_1, booking_lines, booking_lines_fields_info
    )
    write_worksheet(
        "Booking Lines Data",
        workbook,
        worksheet_2,
        booking_line_datas,
        booking_line_datas_fields_info,
    )

    # Save workbook
    workbook.close()
    print(f"#806 File is saved on local - {file_path}")

    # Uploading file to sharepoint
    print("#807 Uploading file to sharepoint...")
    result = upload_file_to_sharepoint(local_filepath, file_name)

    if result:
        print("#808 Uploaded to sharepoint!")

    update_modified_timestamp(mysqlcon, pk_booking_ids)


if __name__ == "__main__":
    print("#900 - Started %s" % datetime.now())
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
        option = get_option(mysqlcon, "web_2_fm_modified")

        if int(option["option_value"]) == 0:
            print("#905 - `web_2_fm_modified` option is OFF")
        elif option["is_running"]:
            print("#905 - `web_2_fm_modified` script is already RUNNING")
        else:
            print("#906 - `web_2_fm_modified` option is ON")
            set_option(mysqlcon, "web_2_fm_modified", True)
            print("#910 - Processing...")

            do_process(mysqlcon, option)

            # Turn off self flag
            _trun_off_flag(mysqlcon, "web_2_fm_modified")
            set_option(mysqlcon, "web_2_fm_modified", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "web_2_fm_modified", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.now())
