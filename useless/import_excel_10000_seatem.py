# Python 3.6.6
import sys, time
import os
import errno
import datetime
from datetime import time
from datetime import date
import uuid
import redis
import urllib, requests
import json
import pymysql, pymysql.cursors
from xlrd import open_workbook
import xlrd

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = 'fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
    # DB_NAME = 'dme_db_prod'  # Prod
else:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = 'root'
    DB_PORT = 3306
    DB_NAME = 'deliver_me'

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

    with mysqlcon.cursor() as cursor:
        book = open_workbook('Seatem July 2018-Jan 2019 as of 25-02-2019_rev2.xlsx')
        sheet = book.sheet_by_index(0)

        # read header values into the list    
        keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]
        dict_list = []
        visual_id = 92000

        for row_index in range(22, sheet.nrows):
            try:
                date_values = xlrd.xldate_as_tuple(sheet.cell(row_index, 12).value, book.datemode)
                date_values = date(*date_values[:3])
            except TypeError:
                date_values = ''

            try:
                date_values2 = xlrd.xldate_as_tuple(sheet.cell(row_index, 4).value, book.datemode)
                date_values2 = date(*date_values2[:3])
            except TypeError:
                date_values2 = ''

            sql = "INSERT INTO `dme_bookings` \
                (`vx_freight_provider`, `z_api_issue_update_flag_500`, `b_client_name`, \
                `b_status`, `v_FPBookingNumber`, `de_To_Address_PostalCode`, \
                `b_bookingID_Visual`, `b_clientReference_RA_Numbers`, `vx_serviceName`, \
                `pu_Address_Suburb`, `pu_Address_State`, `pu_Address_PostalCode`, \
                `de_To_Address_Suburb`, `puCompany`, `puPickUpAvailFrom_Date`, \
                `b_status_API`, `s_21_ActualDeliveryTimeStamp`, `fk_client_warehouse_id`) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \
                %s, %s, %s, %s, %s, %s, %s, %s)"

            cursor.execute(sql, \
                ("Allied", "1", "Seaway", \
                "Booked", str(sheet.cell(row_index, 2).value), str(int(sheet.cell(row_index, 10).value)), \
                str(visual_id), str(int(sheet.cell(row_index, 1).value)), str(sheet.cell(row_index, 5).value), \
                str(sheet.cell(row_index, 6).value), str(sheet.cell(row_index, 7).value), str(int(sheet.cell(row_index, 8).value)), \
                str(sheet.cell(row_index, 9).value), "SEATEM", str( date_values2), \
                str(sheet.cell(row_index, 11).value), str(date_values) + ' 15:00:00', '8'))
            mysqlcon.commit()

            visual_id += 1

    print('#999 - Finished %s' % datetime.datetime.now())
