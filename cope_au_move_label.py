# Python 3.6.6

import sys, time
import os
import errno
import datetime
import uuid
import redis
import urllib, requests
import json
import pymysql, pymysql.cursors
import shutil
import glob
import ntpath

env_mode = 1 # Local
# env_mode = 1 # Dev
# env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = 'root'
    DB_PORT = 3306
    DB_NAME = 'deliver_me'
if env_mode == 1:
    DB_HOST = 'fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
elif env_mode == 2:
    DB_HOST = 'fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_prod'  # Prod

redis_host = "localhost"
redis_port = 6379
redis_password = ""

def get_is_runnable():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `option_value` FROM `dme_options` WHERE `option_name`=%s"
        cursor.execute(sql, ('rename_move_label'))
        result = cursor.fetchone()
        return int(result['option_value'])

def get_filename(filename, visual_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pu_Address_State`, `b_client_sales_inv_num`  FROM `dme_bookings` WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (visual_id))
        result = cursor.fetchone()
        if result is None:
            print('@102 - booking is not exist with this visual_id: ', visual_id)
            return None
        else:
            new_filename = result['pu_Address_State'] + '_' + result['b_client_sales_inv_num'] + '_' + filename
            print('@103 - New filename: ', new_filename)
            return new_filename

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

    can_run = get_is_runnable()

    if can_run > 0:
        if env_mode == 0:
            source_url = "/Users/admin/work/goldmine/scripts/dir01/"
            dest_url_0 = "/Users/admin/work/goldmine/scripts/dir02/"
            dest_url_1 = dest_url_0
            dup_url = "/Users/admin/work/goldmine/scripts/dir_dups/"
        else:
            source_url = "/home/cope_au/dme_sftp/cope_au/labels/indata/"
            dest_url_0 = "/home/cope_au/dme_sftp/cope_au/labels/archive/"
            dest_url_1 = "/var/www/html/dme_api/statics/pdfs/"
            dup_url = "/home/cope_au/dme_sftp/cope_au/labels/duplicates/"

        for file in glob.glob(os.path.join(source_url, "*.pdf")):
            filename = ntpath.basename(file)
            visual_id = int(filename[3:].split('.')[0])
            new_filename = get_filename(filename, visual_id)
            print('@100 - File name: ', filename, 'Visual ID: ', visual_id) 

            if new_filename:
                exists = os.path.isfile(dest_url_0 + new_filename)

                if exists:
                    shutil.move(source_url + filename, dup_url + new_filename)
                    with mysqlcon.cursor() as cursor:
                        sql = "UPDATE `dme_bookings` set `b_error_Capture` = %s WHERE `b_bookingID_Visual` = %s"
                        cursor.execute(sql, ('Label is duplicated', visual_id))
                else:
                    shutil.copy(source_url + filename, dest_url_0 + new_filename)
                    shutil.move(source_url + filename, dest_url_1 + new_filename)
                    with mysqlcon.cursor() as cursor:
                        sql = "UPDATE `dme_bookings` set `b_status` = %s, `z_label_url` = %s WHERE `b_bookingID_Visual` = %s"
                        cursor.execute(sql, ('Booked CSV', new_filename, visual_id))

        mysqlcon.commit()
    else:
        print('#109 - Flag is 0')

    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
