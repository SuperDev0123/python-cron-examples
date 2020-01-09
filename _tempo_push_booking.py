# Python 3.7.0
# V 2.0
import os, sys, time, json
import datetime
import requests

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

TEMPO_CREDENTIALS = {
    "host_url": "https://globalconnect.tempo.org/",
    "api_url": "https://globalconnect.tempo.org/api/EDIDelivery/Items",
    "username": "Deliver.Me",
    "password": "P93xVv2T",
}


def push_via_api(booking):
    json_booking = {}

    json_booking["bookedDate"] = (
        booking["b_dateBookedDate"].strftime("%Y-%m-%d %H:%M:%S")
        if booking["b_dateBookedDate"]
        else ""
    )
    json_booking["fromState"] = booking["de_To_Address_State"]
    json_booking["toEntity"] = booking["deToCompanyName"]
    json_booking["toPostalCode"] = booking["de_To_Address_PostalCode"]
    json_booking["clientSalesInvoice"] = booking["b_client_sales_inv_num"]
    json_booking["clientOrderNo"] = booking["b_client_order_num"]
    json_booking["freightProvider"] = booking["vx_freight_provider"]
    json_booking["consignmentNo"] = booking["v_FPBookingNumber"]
    json_booking["status"] = booking["b_status"]
    json_booking["bookingID"] = booking["b_bookingID_Visual"]

    json_payload = {"data": [json_booking]}
    headers = {"content-type": "application/json"}
    print("@591 - ", json_payload)
    res = requests.post(
        TEMPO_CREDENTIALS["api_url"],
        auth=(TEMPO_CREDENTIALS["username"], TEMPO_CREDENTIALS["password"]),
        json=json_payload,
        headers=headers,
    )
    print("@592 - ", res.status_code, res.content)
