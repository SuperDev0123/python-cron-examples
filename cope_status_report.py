# Python 3.6.6

import sys, time
import os
import errno
import datetime
import uuid
import urllib, requests
import json
import pymysql, pymysql.cursors
import base64
import shutil

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = 'deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'oU8pPQxh'
    DB_PORT = 3306
    # DB_NAME = 'dme_db_dev'  # Dev
    DB_NAME = 'dme_db_prod'  # Prod
else:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = 'root'
    DB_PORT = 3306
    DB_NAME = 'deliver_me'

def get_v_FPBookingNumber(v_FPBookingNumber):
    # if "_" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("_", "")
    # if "-" in v_FPBookingNumber:
    #     v_FPBookingNumber = v_FPBookingNumber.replace("-", "")

    return v_FPBookingNumber

def get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_dateBookedDate`, `b_status`, `b_status_API`, `pk_booking_id`, \
                      `e_qty_scanned_fp_total`, `z_lock_status`, `pu_Address_PostalCode`, \
                      `de_To_Address_PostalCode`, `b_bookingID_Visual` \
                FROM `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (v_FPBookingNumber))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result

def update_booking(booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
               SET b_status=%s, b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
               WHERE id=%s"
        cursor.execute(sql, (b_status, b_status_API_csv, datetime.datetime.now(), booking['id']))
        mysqlcon.commit()

def create_status_history(booking, b_status, event_time_stamp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "INSERT INTO `dme_status_history` \
                (`fk_booking_id`, `status_old`, \
                 `notes`, `status_last`, \
                 `z_createdTimeStamp`, `event_time_stamp`, `recipient_name`, `status_update_via`, `b_booking_visualID` ) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (booking['pk_booking_id'], booking['b_status'],
                             str(booking['b_status']) + " ---> " + str(b_status), b_status,
                             datetime.datetime.now(), event_time_stamp, ' ', 'fp api', booking['b_bookingID_Visual']))
        mysqlcon.commit()

def do_translate_status(booking, b_status_API_csv, v_FPBookingNumber, event_time_stamp, mysqlcon, is_overridable=False):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
              WHERE LOWER(`fp_name`)=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, ('cope'))
        fp_statuses = cursor.fetchall()

        ind = 0
        for fp_status in fp_statuses:
            if fp_status['fp_lookup_status'] and fp_status['fp_lookup_status'] in b_status_API_csv:
                break
            ind = ind + 1

        b_status = fp_statuses[ind]['dme_status']
        is_status = fp_statuses[ind]['if_scan_total_in_booking_greaterthanzero']

        if is_overridable:
            update_booking(booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon)
            create_status_history(booking, b_status, event_time_stamp, mysqlcon)
        else:
            if booking['e_qty_scanned_fp_total'] and booking['e_qty_scanned_fp_total'] > 0:
                b_status = is_status
                update_booking(booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, event_time_stamp, mysqlcon)
            else:
                update_booking(booking, b_status, b_status_API_csv, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, event_time_stamp, mysqlcon)

        if b_status == 'Delivered':
            sql = "SELECT * \
                    FROM `utl_fp_delivery_times` \
                    WHERE `postal_code_from`=%s and `postal_code_to`=%s"
            cursor.execute(sql, (booking['pu_Address_PostalCode'], booking['de_To_Address_PostalCode']))
            result = cursor.fetchone()

            if result:
                delivery_kpi_days = result['delivery_days']
            else:
                delivery_kpi_days = 14

            delivery_days_from_booked = (event_time_stamp - booking['b_dateBookedDate']).days
            delivery_actual_kpi_days = delivery_days_from_booked - delivery_kpi_days

            sql = "UPDATE `dme_bookings` \
               SET s_21_ActualDeliveryTimeStamp=%s, delivery_kpi_days=%s, delivery_days_from_booked=%s, delivery_actual_kpi_days=%s \
               WHERE id=%s"
            cursor.execute(sql, (event_time_stamp, delivery_kpi_days, delivery_days_from_booked, delivery_actual_kpi_days, booking['id']))
            mysqlcon.commit()

            if b_status_API_csv == 'Proof of Delivery':
                sql = "UPDATE `dme_bookings` \
                   SET rpt_proof_of_del_from_csv_time=%s \
                   WHERE id=%s"
                cursor.execute(sql, (datetime.datetime.now(), booking['id']))
                mysqlcon.commit()

def is_b_status_API_csv(booking, b_status_API_csv, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
                WHERE LOWER(`fp_name`)=%s"
        cursor.execute(sql, ('cope'))
        fp_statuses = cursor.fetchall()

        is_new = True
        for fp_status in fp_statuses:
            if fp_status['fp_lookup_status'] and fp_status['fp_lookup_status'] in b_status_API_csv:
                is_new = False
                break

        return is_new

def is_overridable(b_status_API_csv, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
              WHERE `pod_delivery_override`=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, (1))
        fp_statuses = cursor.fetchall()

        bool_val = False
        for fp_status in fp_statuses:
            if fp_status['fp_original_status'] == b_status_API_csv:
                bool_val = True
                break

        return bool_val


def update_status(fpath, mysqlcon):
    with open(fpath) as csv_file:
        with mysqlcon.cursor() as cursor:
            for i, line in enumerate(csv_file):
                v_FPBookingNumber = get_v_FPBookingNumber(line.split(',')[0])
                # new_v_FPBookingNumber = v_FPBookingNumber.replace("DME", "DME_")
                b_status_API_csv = line.split(',')[1]

                if '-' in line.split(',')[2]:
                    event_time_stamp = datetime.datetime.strptime(\
                        line.split(',')[2] + ' ' + line.split(',')[3].replace('\n', ''), '%Y-%m-%d %H:%M')
                else:
                    event_time_stamp = datetime.datetime.strptime(\
                        line.split(',')[2] + ' ' + line.split(',')[3].replace('\n', ''), '%d/%m/%y %H:%M')

                booking = get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon)

                if not booking:
                    print('@102 v_FPBookingNumber not match: ', v_FPBookingNumber)
                else:
                    print('@103 v_FPBookingNumber match: ', v_FPBookingNumber, event_time_stamp)

                    if is_b_status_API_csv(booking, b_status_API_csv, mysqlcon):
                        sql = "UPDATE `dme_bookings` \
                               SET z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                               WHERE id=%s"
                        cursor.execute(sql, ('New Status from FP (' + b_status_API_csv + ') ' + str(datetime.datetime.now().strftime("%d/%m/%Y")), datetime.datetime.now(), booking['id']))
                        mysqlcon.commit()
                    else:
                        if booking['z_lock_status']:
                            if (is_overridable(b_status_API_csv, mysqlcon) 
                                and booking['b_status_API'] == b_status_API_csv):
                                print('@70 - ')
                                sql = "UPDATE `dme_bookings` \
                                       SET z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(sql, ('status was locked with (' + booking['b_status'] + ') - POD Received not set', datetime.datetime.now(), booking['id']))
                                mysqlcon.commit()
                            else:
                                print('@71 - ')
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_status_process_notes=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(sql, (b_status_API_csv, 'status was locked with (' + booking['b_status'] + ') - api status changed but not b_status', datetime.datetime.now(), booking['id']))
                                mysqlcon.commit()
                            create_status_history(booking, 'Locked', event_time_stamp, mysqlcon)
                        else:
                            if (booking['b_status_API'] == 'POD Received' 
                                and is_overridable(b_status_API_csv, mysqlcon) 
                                and booking['b_status_API'] != b_status_API_csv):
                                print('@80 - ')
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(sql, (b_status_API_csv, datetime.datetime.now(), booking['id']))
                                mysqlcon.commit()
                                do_translate_status(booking, b_status_API_csv, v_FPBookingNumber, event_time_stamp, mysqlcon, True)
                            elif (booking['b_status_API'] != 'POD Received' 
                                and booking['b_status_API'] != b_status_API_csv):
                                print('@81 - ')
                                sql = "UPDATE `dme_bookings` \
                                       SET b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(sql, (b_status_API_csv, datetime.datetime.now(), booking['id']))
                                mysqlcon.commit()
                                do_translate_status(booking, b_status_API_csv, v_FPBookingNumber, event_time_stamp, mysqlcon, False)
                            else:
                                print('@82 - ')
                                sql = "UPDATE `dme_bookings` \
                                       SET z_lastStatusAPI_ProcessedTimeStamp=%s \
                                       WHERE id=%s"
                                cursor.execute(sql, (datetime.datetime.now(), booking['id']))
                                mysqlcon.commit()

if __name__ == '__main__':
    print('#900 - Running %s' % datetime.datetime.now())
    
    try:
        mysqlcon = pymysql.connect(host=DB_HOST,
                                   port=DB_PORT,
                                   user=DB_USER,
                                   password=DB_PASS,
                                   db=DB_NAME,
                                   charset='utf8mb4',
                                   cursorclass=pymysql.cursors.DictCursor)
    except:
        print('Mysql DB connection error!')
        exit(1)

    if production:
        CSV_DIR = '/home/cope_au/dme_sftp/cope_au/tracking_status/indata/'
        ARCHIVE_DIR = '/home/cope_au/dme_sftp/cope_au/tracking_status/archive/'
    else:
        CSV_DIR = '/Users/admin/work/goldmine/scripts/dir01/'
        ARCHIVE_DIR = '/Users/admin/work/goldmine/scripts/dir02/'

    if not os.path.isdir(CSV_DIR):
        print('Given argument "%s" is not a directory' % CSV_DIR)
        exit(1)

    try:
        for fname in os.listdir(CSV_DIR):
            fpath = os.path.join(CSV_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith('.csv'):
                print('@100 Detect csv file:', fpath)
                update_status(fpath, mysqlcon)
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print('@109 Moved csv file:', fpath)

    except OSError as e:
        print(str(e))

    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
