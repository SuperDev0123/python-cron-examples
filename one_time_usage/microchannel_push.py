# Python 3.7.0

import os, sys, time
import datetime
import json
import pymysql, pymysql.cursors
import base64
import requests
from zeep import Client
from zeep.wsse.username import UsernameToken
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport
from requests import Session
from requests_ntlm import HttpNtlmAuth

production = True  # Dev
# production = False # Local

if production:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
    # DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def get_booking(b_bookingID_Visual, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `pk_booking_id`, `b_dateBookedDate`, `b_status`, `b_status_API`, \
                `vx_freight_provider`, `v_FPBookingNumber`, `s_21_Actual_Delivery_TimeStamp`, `z_calculated_ETA`, \
                `z_label_url`, `z_pod_url`, `z_pod_signed_url`, `puPickUpAvailFrom_Date`, `pu_PickUp_Avail_Time_Hours`, \
                `pu_PickUp_Avail_Time_Minutes`, `b_client_sales_inv_num` \
                From `dme_bookings` \
                WHERE `b_bookingID_Visual`=%s"
        cursor.execute(sql, (b_bookingID_Visual))
        booking = cursor.fetchone()

        return booking


def get_as_base64(url):
    url = f"/opt/s3_public/imgs/{url}"
    return base64.b64encode(open(url, "rb").read())


def do_process(b_bookingID_Visual, mysqlcon):
    booking = get_booking(b_bookingID_Visual, mysqlcon)

    data = {
        "ShipmentNo": booking["pk_booking_id"],
        "FreightProvider": booking["vx_freight_provider"],
        "ConNoteNo": booking["v_FPBookingNumber"],
        "ShippingCost": None,
        "CollectedDatetime": None,
        "DeliveredDatetime": None,
        "BookingURL": f"http://13.55.160.158/booking?bookingid={booking['id']}",
        "Status": booking["b_status"],
        # "Eta": None,
        # "Label": None,
    }

    if booking["s_21_Actual_Delivery_TimeStamp"]:
        data["DeliveredDatetime"] = booking["s_21_Actual_Delivery_TimeStamp"].strftime(
            "%Y-%m-%d"
        )

    # if booking["z_calculated_ETA"]:
    #     data["Eta"] = booking["z_calculated_ETA"].strftime("%Y-%m-%d %H:%M:%S")

    # if booking["z_label_url"]:
    #     data["Label"] = get_as_base64(booking["z_label_url"]).decode("utf-8")

    if booking["puPickUpAvailFrom_Date"]:
        data["CollectedDatetime"] = booking["puPickUpAvailFrom_Date"].strftime(
            "%Y-%m-%d"
        )

    if booking["pu_PickUp_Avail_Time_Hours"]:
        data[
            "CollectedDatetime"
        ] += f" {booking['pu_PickUp_Avail_Time_Hours']}:{booking['pu_PickUp_Avail_Time_Minutes']}"

    if not booking["pu_PickUp_Avail_Time_Minutes"]:
        data["CollectedDatetime"] += "0"

    session = Session()
    session.auth = HttpNtlmAuth("WIN-E078025RB70\\administrator", "Mic1234!")

    client = Client(
        "http://220.244.34.10:7047/DynamicsNAV100/WS/Codeunit/DeliverMeWS",
        transport=Transport(session=session),
    )

    print("@1 client:", client)
    print("@2 data:", json.dumps(data))
    r = client.service.UpdateShipmentDetails(jsonText=json.dumps(data))
    print("@3 - ", r)

    if booking["b_status"] == "Delivered" and booking["z_pod_url"]:
        data0 = {
            "ShipmentNo": booking["pk_booking_id"],
            "DocType": "ProofOfDelivery",
            "Extension": "png",
            "Base64Text": None,
        }

        data0["Base64Text"] = get_as_base64(booking["z_pod_url"]).decode("utf-8")

        print("@101 data:", json.dumps(data0))
        r0 = client.service.UpdateDocument(jsonText=json.dumps(data0))
        print("@102 - ", r0)


if __name__ == "__main__":
    b_bookingID_Visual = sys.argv[1]
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
        do_process(b_bookingID_Visual, mysqlcon)
    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
