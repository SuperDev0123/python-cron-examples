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

env_mode = 0 # Local
# env_mode = 1 # Dev
# env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = 'root'
    DB_PORT = 3306
    DB_NAME = 'deliver_me'
if env_mode == 1:
    DB_HOST = 'deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'oU8pPQxh'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
elif env_mode == 2:
    DB_HOST = 'deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'oU8pPQxh'
    DB_PORT = 3306
    DB_NAME = 'dme_db_prod'  # Prod

redis_host = "localhost"
redis_port = 6379
redis_password = ""

def get_filename(filename, visual_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `pu_Address_State`, `b_client_sales_inv_num` FROM `dme_bookings` WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (visual_id))
        result = cursor.fetchone()
        if result is None:
            print('@102 - booking is not exist with this visual_id: ', visual_id)
            return None
        else:
            new_filename = 'POD_' + result['pu_Address_State'] + '_' + result['b_client_sales_inv_num'] + '_' + filename
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

    if env_mode == 0:
        source_url = "/Users/admin/work/goldmine/scripts/dir01/"
        dest_url_0 = "/Users/admin/work/goldmine/scripts/dir02/"
        dest_url_1 = dest_url_0
        dup_url = "/Users/admin/work/goldmine/scripts/dir_dups/"
    else:
        source_url = "/home/cope_au/dme_sftp/cope_au/pods/indata/"
        dest_url_0 = "/home/cope_au/dme_sftp/cope_au/pods/archive/"
        dest_url_1 = "/var/www/html/dme_api/static/imgs/"
        dup_url = "/home/cope_au/dme_sftp/cope_au/pods/duplicates/"

    for file in glob.glob(os.path.join(source_url, "*.png")):
        filename = ntpath.basename(file)

        if '_' in filename:
            visual_id = int(filename.split('_')[1].split('.')[0])
        else:
            visual_id = int(filename[3:].split('.')[0])

        new_filename = get_filename(filename, visual_id)
        print('@100 - File name: ', filename, 'Visual ID: ', visual_id, 'New name:', new_filename) 

        if new_filename:
            exists = os.path.isfile(dest_url_0 + new_filename)

            if exists:
                shutil.move(source_url + filename, dup_url + new_filename)
                with mysqlcon.cursor() as cursor:
                    sql = "UPDATE `dme_bookings` set `b_error_Capture` = %s WHERE `b_bookingID_Visual` = %s"
                    cursor.execute(sql, ('POD is duplicated', visual_id))
                mysqlcon.commit()
            else:
                shutil.copy(source_url + filename, dest_url_0 + new_filename)
                shutil.move(source_url + filename, dest_url_1 + new_filename)
                with mysqlcon.cursor() as cursor:
                    sql = "UPDATE `dme_bookings` set `z_pod_url` = %s WHERE `b_bookingID_Visual` = %s"
                    cursor.execute(sql, (new_filename, visual_id))
                mysqlcon.commit()
        
    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
