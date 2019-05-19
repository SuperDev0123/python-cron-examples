# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil

production = True # Dev
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

def get_api_bcl(label_code, client_item_reference, mysqlcon):
     with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `fk_booking_id`, `fk_booking_line_id`, `fp_event_date`, `tally` \
                FROM `api_booking_confirmation_lines` \
                WHERE `label_code`=%s and `client_item_reference`=%s"
        cursor.execute(sql, (label_code, client_item_reference))
        result = cursor.fetchone()
        return result

def update_qty_scanned(cnt, fk_booking_id, fk_booking_line_id, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE `dme_booking_lines` \
            SET `e_qty_scanned_fp`=%s \
            WHERE `pk_lines_id`=%s"
        cursor.execute(sql, (cnt, fk_booking_line_id))
        mysqlcon.commit()

        sql = "SELECT `e_qty_scanned_fp` \
                From `dme_booking_lines` \
                WHERE `fk_booking_id`=%s"
        cursor.execute(sql, (fk_booking_id))
        booking_lines = cursor.fetchall()

        e_qty_scanned_fp_total = 0
        for booking_line in booking_lines:
            if booking_line['e_qty_scanned_fp']:
                e_qty_scanned_fp_total = e_qty_scanned_fp_total + int(booking_line['e_qty_scanned_fp'])

        sql = "UPDATE `dme_bookings` \
            SET `e_qty_scanned_fp_total`=%s \
            WHERE `pk_booking_id`=%s"
        cursor.execute(sql, (e_qty_scanned_fp_total, fk_booking_id))
        mysqlcon.commit()

def update_tally(api_bcl, mysqlcon):
    if api_bcl['fp_event_date']:
        if api_bcl['tally']:
            tally = int(api_bcl['tally']) + 1
        else:
            tally = 1

        with mysqlcon.cursor() as cursor:
            sql = "UPDATE `api_booking_confirmation_lines` \
                    SET tally=%s \
                    WHERE `id`=%s "
            cursor.execute(sql, (tally, api_bcl['id']))
            mysqlcon.commit()

def do_process(fpath, mysqlcon):
    cnt = 0
    old_label_code = ''
    old_client_item_reference = ''
    old_fk_booking_id = ''
    old_fk_booking_line_id = ''
    cvs_line_cnt = len(open(fpath).readlines())
    processed_label_code = []

    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            if i % 1000 == 0:
                print('#', i)
            label_code = line.split(',')[0]
            client_item_reference = line.split(',')[1].split(' ')[1]

            if client_item_reference is not '':
                api_bcl = get_api_bcl(label_code, client_item_reference, mysqlcon)

                if api_bcl:
                    fp_event_date = datetime.datetime.strptime(line.split(',')[2], '%Y-%m-%d')
                    fp_event_time = datetime.datetime.strptime(line.split(',')[3] + ':00', '%H:%M:%S')
                    fp_scan_data = line.split(',')[4].split(' ')[2]

                    if cnt == 0:
                        # Reset Olds
                        old_label_code = label_code
                        old_client_item_reference = client_item_reference
                        old_fk_booking_id = api_bcl['fk_booking_id']
                        old_fk_booking_line_id = api_bcl['fk_booking_line_id']

                    if i == 0:
                        old_label_code = label_code
                        old_client_item_reference = client_item_reference
                        old_fk_booking_id = api_bcl['fk_booking_id']
                        old_fk_booking_line_id = api_bcl['fk_booking_line_id']
                        cnt = cnt + 1
                        processed_label_code.append(label_code)

                    if (cnt > 0 and \
                        (label_code[3:-3] != old_label_code[3:-3] or \
                        client_item_reference != old_client_item_reference)) or \
                        i == cvs_line_cnt - 1:

                        if (i == cvs_line_cnt - 1):
                            if not label_code in processed_label_code:
                                update_qty_scanned(cnt + 1, old_fk_booking_id, old_fk_booking_line_id, mysqlcon)
                            else:
                                update_qty_scanned(cnt, old_fk_booking_id, old_fk_booking_line_id, mysqlcon)
                        else:
                            update_qty_scanned(cnt, old_fk_booking_id, old_fk_booking_line_id, mysqlcon)

                        # Reset Olds
                        old_label_code = label_code
                        old_client_item_reference = client_item_reference
                        old_fk_booking_id = api_bcl['fk_booking_id']
                        old_fk_booking_line_id = api_bcl['fk_booking_line_id']
                        cnt = 0
                        processed_label_code = []

                    update_tally(api_bcl, mysqlcon)

                    with mysqlcon.cursor() as cursor:
                        sql = "UPDATE `api_booking_confirmation_lines` \
                                SET fp_event_date=%s, fp_event_time=%s, fp_scan_data=%s \
                                WHERE `label_code`=%s and `client_item_reference`=%s"
                        cursor.execute(sql, (fp_event_date, fp_event_time, fp_scan_data, label_code, client_item_reference))
                        mysqlcon.commit()

                    if not label_code in processed_label_code:
                        cnt = cnt + 1
                        processed_label_code.append(label_code)
                else:
                    update_qty_scanned(cnt, old_fk_booking_id, old_fk_booking_line_id, mysqlcon)
                    cnt = 0
                    processed_label_code = []
                    # print('@209 - No matching BCL - label_code: ', label_code, ' Line of CSV: ', str(i + 1))

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
        CSV_DIR = '/home/cope_au/dme_sftp/cope_au/scans_labels/indata/'
        ARCHIVE_DIR = '/home/cope_au/dme_sftp/cope_au/scans_labels/archive/'
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
                do_process(fpath, mysqlcon)
                shutil.move(CSV_DIR + fname, ARCHIVE_DIR + fname)
                print('@109 Moved csv file:', fpath)

    except OSError as e:
        print(str(e))

    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
