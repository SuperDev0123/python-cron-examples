# Python 3.7.0
# V 2.0
import os, sys, time, json
import datetime
import requests

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
    json_booking["fromState"] = booking["pu_Address_State"]
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
    json_booking["deToAddress"] = (
        booking["de_To_Address_Street_1"] + ""
        if booking["de_To_Address_Street_2"]
        else booking["de_To_Address_Street_1"]
    )
    json_booking["deToPhoneMain"] = booking["de_to_Phone_Main"]
    json_booking["deToAddressSuburb"] = booking["de_To_Address_Suburb"]
    json_booking["deToAddressState"] = booking["de_To_Address_State"]
    # json_booking["dhlOrder"] = booking["de_To_Address_PostalCode"]

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
