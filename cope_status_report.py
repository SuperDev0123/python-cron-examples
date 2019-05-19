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
        sql = "SELECT `id`, `b_dateBookedDate`, `b_status`, `b_status_API`, `pk_booking_id`, `e_qty_scanned_fp_total` \
                FROM `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (v_FPBookingNumber))
        result = cursor.fetchone()
        # print('@102 - ', result)
        return result

def update_booking(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_bookings` \
               SET b_status=%s, b_status_API=%s, z_lastStatusAPI_ProcessedTimeStamp=%s \
               WHERE id=%s"
        cursor.execute(sql, (b_status, new_status_API, datetime.datetime.now(), booking['id']))
        mysqlcon.commit()

def do_translate_status(booking, new_status_API, new_v_FPBookingNumber, event_time_stamp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * FROM `dme_utl_fp_statuses` \
              WHERE LOWER(`fp_name`)=%s \
              ORDER BY `id` ASC"
        cursor.execute(sql, ('cope'))
        fp_statuses = cursor.fetchall()

        is_status_exist = False
        ind = 0
        for fp_status in fp_statuses:
            if fp_status['fp_lookup_status'] and fp_status['fp_lookup_status'] in new_status_API:
                is_status_exist = True
                break
            ind = ind + 1

        if not is_status_exist:
            sql = "INSERT INTO `dme_utl_fp_statuses` \
                (`fp_name`, `fp_original_status`, `fp_lookup_status`, `dme_status`) \
                VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, ('COPE', new_status_API, new_status_API, 'Pickup ' + new_status_API))
            mysqlcon.commit()
            b_status = 'api status'
        else:
            b_status = fp_statuses[ind]['dme_status']

        if b_status == 'In Transit' and booking['e_qty_scanned_fp_total'] and booking['e_qty_scanned_fp_total'] > 0:
            if new_status_API == 'Out For Delivery' or new_status_API == 'Proof of Delivery':
                update_booking(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
        elif b_status == 'In Transit' and (not booking['e_qty_scanned_fp_total'] or booking['e_qty_scanned_fp_total'] == 0):
            if new_status_API == 'Out For Delivery' or new_status_API == 'Proof of Delivery':
                update_booking(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
        elif b_status is not 'In Transit':
            if (new_status_API == 'Allocated' or new_status_API == 'NEW') and booking['e_qty_scanned_fp_total'] > 0:
                update_booking(booking, 'In Transit', new_status_API, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
            elif new_status_API != 'Allocated' and new_status_API != 'NEW':
                update_booking(booking, b_status, new_status_API, event_time_stamp, mysqlcon)
                create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon)

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
            create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon)

def create_status_history(booking, b_status, new_status_API, event_time_stamp, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "INSERT INTO `dme_status_history` (`fk_booking_id`, `status_old`, `notes`, `status_last`, \
              `z_createdTimeStamp`, `event_time_stamp`, `recipient_name`, `status_update_via`) \
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, 
                        (booking['pk_booking_id'], booking['b_status'],
                         str(booking['b_status']) + " ---> " + str(b_status), b_status,
                         datetime.datetime.now(), event_time_stamp, ' ', 'fp api'))
        mysqlcon.commit()

def update_status(fpath, mysqlcon):
    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            v_FPBookingNumber = get_v_FPBookingNumber(line.split(',')[0])
            new_v_FPBookingNumber = v_FPBookingNumber.replace("DME", "DME_")
            new_status_API = line.split(',')[1]

            if '-' in line.split(',')[2]:
                event_time_stamp = datetime.datetime.strptime(\
                    line.split(',')[2] + ' ' + line.split(',')[3].replace('\n', ''), '%Y-%m-%d %H:%M')
            else:
                event_time_stamp = datetime.datetime.strptime(\
                    line.split(',')[2] + ' ' + line.split(',')[3].replace('\n', ''), '%d/%m/%y %H:%M')

            booking = get_booking_with_v_FPBookingNumber(v_FPBookingNumber, mysqlcon)

            if booking:
                print('@103 v_FPBookingNumber match: ', v_FPBookingNumber, event_time_stamp)

                if booking['b_status_API'] != new_status_API and not booking['z_lock_status']:
                    b_status = do_translate_status(booking, new_status_API, new_v_FPBookingNumber, event_time_stamp, mysqlcon)
                else:
                    with mysqlcon.cursor() as cursor:
                        sql = "UPDATE `dme_bookings` \
                               SET z_lastStatusAPI_ProcessedTimeStamp=%s \
                               WHERE id=%s"
                        cursor.execute(sql, (datetime.datetime.now(), booking['id']))
                        mysqlcon.commit()
                    print('@105 has same status_api or z_lock_status is 1')
            else:
                print('@104 v_FPBookingNumber not match: ', v_FPBookingNumber)

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

# get the b_status from b_status_api
# if b_status is not same as new_status and z_lock_status is false
#     if b_status is `In Transit` and scanned
#         if new_status is 'Out For Delivery` or `Proof of Delivery -> b_status = new_status
#         else do nothing
#     else if b_status is `In Transit` and scanned_total = 0:
#         b_status -> b_status = new_status
#     else if b_status is not `In Transit`
#         if new_status is `Allocated` or `New` and scanned_total > 0 -> b_status = `In Transit`
#         else if new_status is not `Allocated` or `New` -> b_status = new_status
# else
#     update dme_bookings/z_lastStatusAPI_ProcessedTimeStamp
