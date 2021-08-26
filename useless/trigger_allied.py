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

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = 'fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
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
        sql = "SELECT * FROM `dme_bookings` WHERE LOWER(`vx_freight_provider`)=%s and `z_api_issue_update_flag_500`=%s and `b_client_name`=%s ORDER BY `id` ASC LIMIT %s"
        cursor.execute(sql, ('allied', '1', 'Seaway', 10))
        booking_list = cursor.fetchall()

    print('@1 - ', len(booking_list))
    print('@10 - ', booking_list[0])
    # booking_list = Bookings.objects.filter(vx_freight_provider="Allied",
    #                                        z_api_issue_update_flag_500=1, b_client_name="Seaway",
    #                                        b_status_API__isnull=True)
    results = []

    for booking in booking_list:
        url = "http://35.161.204.104:8081/dme-api/tracking/trackconsignment"
        data = {}
        print("==============")
        print(booking['v_FPBookingNumber'])
        print(booking['deToAddressPostalCode'])
        data['consignmentDetails'] = [{"consignmentNumber": booking['v_FPBookingNumber'],
                                       "destinationPostcode": booking['deToAddressPostalCode']}]
        data['spAccountDetails'] = {"accountCode": "DELVME", "accountState": "NSW",
                                    "accountKey": "ce0d58fd22ae8619974958e65302a715"}
        data['serviceProvider'] = "ALLIED"

        response0 = requests.post(url, params={}, json=data)
        response0 = response0.content.decode('utf8').replace("'", '"')
        data0 = json.loads(response0)
        s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
        print('@2 - ', s0)
        try:
            request_payload = {"apiUrl": '', 'accountCode': '', 'authKey': '', 'trackingId': ''};
            request_payload["apiUrl"] = url
            request_payload["accountCode"] = data["spAccountDetails"]["accountCode"]
            request_payload["authKey"] = data["spAccountDetails"]["accountKey"]
            request_payload["trackingId"] = data["consignmentDetails"][0]["consignmentNumber"]
            request_type = "TRACKING"
            request_status = "SUCCESS"

            with mysqlcon.cursor() as cursor:
                sql = "INSERT INTO `dme_log` (`request_payload`, `request_status`, `request_type`, `response`, `fk_booking_id`) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (request_payload, request_status, request_type, response0, booking.id))
                mysqlcon.commit()

            try:
                booking.b_status_API = data0['consignmentTrackDetails'][0]['consignmentStatuses'][0]['status']
                booking.z_lastStatusAPI_ProcessedTimeStamp = datetime.datetime.now()
                if data0['consignmentTrackDetails'][0]['consignmentStatuses'][0]['status'] == 'Delivered in Full':
                    booking.s_21_ActualDeliveryTimeStamp = datetime.datetime.now()

                booking.save()
                print("yes")
            except IndexError:
                print("no")

            print("==============")
            results.append({"Created Log ID": oneLog.id})
        except KeyError:
            results.append({"Error": "Too many request"})

    print("#901 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
