# Python 3.7

import sys
import os
import errno
import shutil
import datetime
import uuid
import requests
import json
import traceback
import pymysql, pymysql.cursors

# IS_PRODUCTION = False  # Local
IS_PRODUCTION = True  # Prod

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
    # DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = ""
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def check_none(field):
    if isinstance(field, datetime.date):
        return str(field)

    return field if field else ""


def build_json(mysqlcon):
    cursor = mysqlcon.cursor()

    # Fetch a booking
    sql = "SELECT * \
            FROM dme_bookings \
            WHERE b_bookingID_Visual=%s"
    cursor.execute(sql, (89606))
    booking = cursor.fetchone()

    # Fetch related booking_line
    sql = "SELECT * \
            FROM dme_booking_lines \
            WHERE fk_booking_id=%s"
    cursor.execute(sql, (booking["pk_booking_id"]))
    booking_lines = cursor.fetchall()

    # Fetch a Warehouse
    sql = "SELECT * \
            FROM dme_client_warehouses \
            WHERE pk_id_client_warehouses=%s"
    cursor.execute(sql, (booking["fk_client_warehouse_id"]))
    warehouse = cursor.fetchone()

    booking_json = {
        "dmeBookingNumber": check_none(booking["b_bookingID_Visual"]),
        "client": check_none(booking["b_client_name"]),
        "subClient": check_none(booking["b_client_name_sub"]),
        "warehouseCode": check_none(warehouse["client_warehouse_code"]),
        "freightProvider": check_none(booking["vx_freight_provider"]),
        "consignmentNoteNumber": check_none(booking["v_FPBookingNumber"]),
        "bookingNotes": check_none(booking["b_booking_Notes"]),
        "driverToBringLabelling": "",
        "returnsPackagingBooking": "",
        "locationCode": "",
        "pickupEntity": check_none(booking["puCompany"]),
        "pickupEntityGroup": "",
        "pickupStreet1": check_none(booking["pu_Address_Street_1"]),
        "pickupStreet2": check_none(booking["pu_Address_street_2"]),
        "pickupState": check_none(booking["pu_Address_State"]),
        "pickupPostalCode": check_none(booking["pu_Address_PostalCode"]),
        "pickupSuburb": check_none(booking["pu_Address_Suburb"]),
        "pickupCountry": check_none(booking["pu_Address_Country"]),
        "pickupContact": check_none(booking["pu_Contact_F_L_Name"]),
        "pickupTel": check_none(booking["pu_Phone_Main"]),
        "pickupMobile": check_none(booking["pu_Phone_Mobile"]),
        "pickupEmail": check_none(booking["pu_Email"]),
        "pickupFrom": check_none(booking["puPickUpAvailFrom_Date"]),
        "pickupBy": check_none(booking["pu_PickUp_By_Date"]),
        "pickupInstructions": check_none(booking["pu_pickup_instructions_address"]),
        "tailLift": check_none(booking["b_booking_tail_lift_pickup"]),
        "peopleNeeded": check_none(booking["b_booking_no_operator_pickup"]),
        "additionalServicesRequired": "",
        "pickupCommunicateVia": check_none(booking["pu_Comm_Booking_Communicate_Via"]),
    }

    booking_lines_json = []
    for booking_line in booking_lines:
        # Fetch a booking_line_data
        sql = "SELECT * \
                FROM dme_booking_lines_data \
                WHERE fk_booking_lines_id=%s"
        cursor.execute(sql, (booking_line["pk_lines_id"]))
        booking_line_data = cursor.fetchone()

        if not booking_line_data:
            booking_line_data = {"modelNumber": "", "itemDescription": ""}

        booking_lines_json.append(
            {
                "itemModelNumber": check_none(booking_line_data["modelNumber"]),
                "itemDescription": check_none(booking_line_data["itemDescription"]),
                "qty": check_none(booking_line["e_qty"]),
                "weightUnitOfMeasure": check_none(booking_line["e_weightUOM"]),
                "weightEachItem": check_none(booking_line["e_weightPerEach"]),
                "dimentionUnitOfMeasure": check_none(booking_line["e_dimUOM"]),
                "length": check_none(booking_line["e_dimLength"]),
                "width": check_none(booking_line["e_dimWidth"]),
                "height": check_none(booking_line["e_dimHeight"]),
                "dangerousGoods": check_none(booking_line["e_dangerousGoods"]),
                "dangerousGoodsCode": "",
            }
        )

    result_json = {"booking": booking_json, "bookingLines": booking_lines_json}
    print(result_json)
    return result_json


if __name__ == "__main__":
    print("#900 Started %s" % datetime.datetime.now())

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
        build_json(mysqlcon)
    except Exception as e:
        print("#901 ", str(e))
        traceback.print_exc()

    print("#999 Finished %s" % datetime.datetime.now())
