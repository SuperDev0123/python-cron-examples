# Python 3.6.6

import sys, time
import os, base64
import errno
import datetime
import uuid
import urllib, requests
import pymysql, pymysql.cursors
import json
import time

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME


def get_missing_products():
    missing_products = []
    with mysqlcon.cursor() as cursor:
        sql = "SELECT DISTINCT parent_model_number FROM client_products"
        #  WHERE  b_status='Ready for XML'
        #  WHERE b_client_name = 'Seaway'
        cursor.execute(sql)
        parent_models = cursor.fetchall()
        for item in parent_models:
            model = item['parent_model_number']
            sql = "SELECT * FROM client_products WHERE parent_model_number=%s AND child_model_number=%s"
            values = (model, model)
            cursor.execute(sql, values)
            result = cursor.fetchone()
            if result is None:
                missing_products.append(model)
    return missing_products


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
        #exit(1)
    missing_products = get_missing_products()
    print('Missing Products', missing_products)
    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
                    
