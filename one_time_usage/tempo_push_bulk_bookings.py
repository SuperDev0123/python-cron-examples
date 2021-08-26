# Python 3.7.0
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = "dme_db_dev"  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

TEMPO_CREDENTIALS = {
    "host_url": "https://globalconnect.tempo.org/",
    "api_url": "https://globalconnect.tempo.org/api/EDIDelivery/Items",
    "username": "Deliver.Me",
    "password": "P93xVv2T",
}


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_bookings` \
                WHERE `kf_client_id`=%s and \
                `b_status` <> 'Ready for Booking' and (`b_status` = 'Closed' or `b_status` = 'Cancelled') \
                ORDER BY id"
        cursor.execute(sql, ("461162D2-90C7-BF4E-A905-092A1A5F73F3"))
        bookings = cursor.fetchall()

        return bookings


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)
    print("@310 - Bookings Cnt:", len(bookings))

    for index in range(int(len(bookings) / 5000) + 1):  # Batch - 5000
        print("@1 - ", index)
        json_bookings = []
        for i in range(index * 5000, (index + 1) * 5000):
            json_booking = {}
            booking = bookings[i]

            try:
                json_booking["bookedDate"] = (
                    booking["b_dateBookedDate"].strftime("%Y-%m-%d %H:%M:%S")
                    if booking["b_dateBookedDate"]
                    else ""
                )
            except Exception as e:
                print(f"{booking['b_bookingID_Visual']}: {e}")
                exit()
            json_booking["fromState"] = booking["de_To_Address_State"]
            json_booking["toEntity"] = booking["deToCompanyName"]
            json_booking["toPostalCode"] = booking["de_To_Address_PostalCode"]
            json_booking["clientSalesInvoice"] = booking["b_client_sales_inv_num"]
            json_booking["clientOrderNo"] = booking["b_client_order_num"]
            json_booking["freightProvider"] = booking["vx_freight_provider"]
            json_booking["consignmentNo"] = booking["v_FPBookingNumber"]
            json_booking["status"] = booking["b_status"]
            json_booking["bookingID"] = booking["b_bookingID_Visual"]
            json_booking["actualDeliveryDate"] = (
                booking["s_21_ActualDeliveryTimeStamp"].strftime("%Y-%m-%d %H:%M:%S")
                if booking["s_21_ActualDeliveryTimeStamp"]
                else ""
            )
            json_booking["bookingRequestDate"] = (
                booking["delivery_booking"].strftime("%Y-%m-%d")
                if booking["delivery_booking"]
                else ""
            )
            json_bookings.append(json_booking)

            if i == len(bookings) - 1:
                break

        json_payload = {"data": json_bookings, "chunk_index": str(index)}
        headers = {"content-type": "application/json"}
        print("@210 - ", len(json_bookings))
        res = requests.post(
            TEMPO_CREDENTIALS["api_url"],
            auth=(TEMPO_CREDENTIALS["username"], TEMPO_CREDENTIALS["password"]),
            json=json_payload,
            headers=headers,
        )
        print("@230 - ", res.status_code, res.content)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())

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
        do_process(mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
