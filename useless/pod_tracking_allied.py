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
        sql = "SELECT * FROM `dme_bookings` WHERE LOWER(`vx_freight_provider`)=%s and `z_api_issue_update_flag_500`=%s " \
              " ORDER BY `id` ASC"
        cursor.execute(sql, ('allied', '1'))
        booking_list = cursor.fetchall()

    print('@1 Bookings cnt - ', len(booking_list))
    # print('@10 - ', booking_list[0])
    # booking_list = Bookings.objects.filter(vx_freight_provider="Allied",
    #                                        z_api_issue_update_flag_500=1, b_client_name="Seaway",
    #                                        b_status_API__isnull=True)
    results = []

    for booking in booking_list:
        print('num : ', booking['pk_booking_id'])
        url = "http://35.161.204.104:8081/dme-api/tracking/trackconsignment"
        data = {}
        data['consignmentDetails'] = [{"consignmentNumber": booking['v_FPBookingNumber'],
                                       "destinationPostcode": booking['de_To_Address_PostalCode']}]
        data['spAccountDetails'] = {"accountCode": "DELVME", "accountState": "NSW",
                                    "accountKey": "ce0d58fd22ae8619974958e65302a715"}
        data['serviceProvider'] = "ALLIED"

        response0 = requests.post(url, params={}, json=data)
        response0 = response0.content.decode('utf8')
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual

        try:
            request_payload = {"apiUrl": '', 'accountCode': '', 'authKey': '', 'trackingId': ''};
            request_payload["apiUrl"] = url
            request_payload["accountCode"] = data["spAccountDetails"]["accountCode"]
            request_payload["authKey"] = data["spAccountDetails"]["accountKey"]
            request_payload["trackingId"] = data["consignmentDetails"][0]["consignmentNumber"]
            request_type = "TRACKING"
            request_status = "SUCCESS"
            print('@10 - ', s0)

            try:
                if booking['z_pod_url'] is None or booking['z_pod_url'] == '':
                    print("now pod.")

                    pod_file = data0['consignmentTrackDetails'][0]["pods"][0]['podData']
                    print("pod is fine.")

                    warehouse_name = ''
                    if warehouse:
                        warehouse_name = warehouse[0]['client_warehouse_code']
                    file_name = "POD_" + \
                                str(warehouse_name) + "_" + \
                                booking['b_clientReference_RA_Numbers'] + "_" + \
                                booking['v_FPBookingNumber'] + "_" + \
                                str(booking['b_bookingID_Visual']) + '.png'
                    file_url = '/var/www/html/dme_api/static/imgs/' + file_name

                    with open(os.path.expanduser(file_url), 'wb') as fout:
                        fout.write(
                            base64.decodestring(pod_file.encode('utf-8')))

                    with mysqlcon.cursor() as cursor:
                        sql = "Update `dme_bookings` set z_pod_url=%s where id =%s"
                        cursor.execute(sql, (file_name, booking['id']))
                        mysqlcon.commit()
            except IndexError:
                print("POD : ", ' empty')

            try:
                if booking['z_pod_signed_url'] is None or booking['z_pod_signed_url'] == '':
                    print("now sign.")
                    pod_file = data0['consignmentTrackDetails'][0]['consignmentStatuses'][0]['signatureImage']
                    print("sign is fine.")
                    warehouse_name = ''
                    if warehouse:
                        warehouse_name = warehouse[0]['client_warehouse_code']
                    file_name = "pod_signed_" + \
                                str(warehouse_name) + "_" + \
                                booking['b_clientReference_RA_Numbers'] + "_" + \
                                booking['v_FPBookingNumber'] + "_" + \
                                str(booking['b_bookingID_Visual']) + '.png'
                    file_url = '/var/www/html/dme_api/static/imgs/' + file_name

                    with open(os.path.expanduser(file_url), 'wb') as fout:
                        fout.write(
                            base64.decodestring(pod_file.encode('utf-8')))

                    with mysqlcon.cursor() as cursor:
                        sql = "Update `dme_bookings` set z_pod_signed_url=%s where id =%s"
                        cursor.execute(sql, (file_name, booking['id']))
                        mysqlcon.commit()
            except IndexError:
                print("sign : ", ' empty')
        except KeyError  as e:
            print("error : ", e)

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()