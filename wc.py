# Python 3.7.0

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import json
import requests

import _status_history
# from _env import (
#     DB_HOST,
#     DB_USER,
#     DB_PASS,
#     DB_PORT,
#     DB_NAME,
# )
from _options_lib import get_option, set_option

from woocommerce import API

wcapi = API(
    url="https://bathroomsalesdirect.com.au/", # Your store URL
    consumer_key="ck_ef5088f8997a8bb637b866269962530c62f2e4e8", # Your consumer key
    consumer_secret="cs_263cbc00a2a180d6bb9d7011194dfc98d04d8377", # Your consumer secret
    wp_api=True, # Enable the WP REST API integration
    version="wc/v3" # WooCommerce WP REST API version
)

DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
DB_USER = "fmadmin"
DB_PASS = "oU8pPQxh"
DB_PORT = 3306
DB_NAME = "dme_db_dev"



def get_orders_from_woocommerce(from_date, to_date):
    try:
        order_list = wcapi.get(f"orders?after={from_date}&before={to_date}").json()
    except Exception as e:
        print('Get orders error: {e}')
        order_list = []

    orders = []
    if order_list:
        for order in order_list:
            booking = {
                id = models.AutoField(primary_key=True)
                b_bookingID_Visual: 0,
                b_dateBookedDate: None,
                puPickUpAvailFrom_Date: None,
                b_clientReference_RA_Numbers: None,
                b_status: None,
                b_status_category: None,
                vx_freight_provider: None,
                vx_serviceName: None,
                s_05_LatestPickUpDateTimeFinal: None,
                s_06_LatestDeliveryDateTimeFinal: None,
                v_FPBookingNumber: None,
                puCompany: None,
                deToCompanyName: order['billing']['company'],
                consignment_label_link: None,
                error_details: None,
                fk_client_warehouse: 1,
                b_clientPU_Warehouse: None,
                is_printed: None,
                shipping_label_base64: None,
                kf_client_id: None,
                b_client_name: None,
                pk_booking_id: None,
                zb_002_client_booking_key: None,
                fk_fp_pickup_id: None,
                pu_pickup_instructions_address: None,
                kf_staff_id: None,
                kf_clientCustomerID_PU: None,
                kf_clientCustomerID_DE: None,
                kf_Add_ID_PU: None,
                kf_Add_ID_DE: None,
                kf_FP_ID: None,
                kf_booking_Created_For_ID: None,
                kf_email_Template: None,
                inv_dme_invoice_no: None,
                kf_booking_quote_import_id: None,
                kf_order_id: None,
                x_Data_Entered_Via: None,
                b_booking_Priority: None,
                z_API_Issue: 0,
                z_api_issue_update_flag_500: False,
                pu_Address_Type: None,
                pu_Address_Street_1: None,
                pu_Address_street_2: None,
                pu_Address_State: None,
                pu_Address_City: None,
                pu_Address_Suburb: None,
                pu_Address_PostalCode: None,
                pu_Address_Country: None,
                pu_Contact_F_L_Name: None,
                pu_Phone_Main: None,
                pu_Phone_Mobile: None,
                pu_Email: None,
                pu_email_Group_Name: None,
                pu_email_Group: None,
                pu_Comm_Booking_Communicate_Via: None,
                pu_Contact_FName: None,
                pu_PickUp_Instructions_Contact: None,
                pu_WareHouse_Number: None,
                pu_WareHouse_Bay: None,
                pu_Contact_Lname: None,
                de_Email: order['billing']['email'],
                de_To_AddressType: None,
                de_To_Address_Street_1: order['billing']['address_1'],
                de_To_Address_Street_2: order['billing']['address_2'],
                de_To_Address_State: order['billing']['state'],
                de_To_Address_City: None,
                de_To_Address_Suburb: order['billing']['city'],
                de_To_Address_PostalCode: order['billing']['postcode'],
                de_To_Address_Country: order['billing']['country'],
                de_to_Contact_F_LName: f"{order['billing']['first_name']} {order['billing']['last_name']}",
                de_to_Contact_FName: order['billing']['first_name'],
                de_to_Contact_Lname: order['billing']['last_name'],
                de_To_Comm_Delivery_Communicate_Via: None,
                de_to_Pick_Up_Instructions_Contact: None,
                de_to_PickUp_Instructions_Address: None,
                de_to_WareHouse_Number: None,
                de_to_WareHouse_Bay: None,
                de_to_Phone_Mobile: None,
                de_to_Phone_Main: order['billing']['phone'],
                de_to_addressed_Saved: 0,
                de_Contact: None,
                pu_PickUp_By_Date: None,
                pu_addressed_Saved: 0,
                b_date_booked_by_dme: None,
                b_booking_Notes: None,
                s_02_Booking_Cutoff_Time: None,
                s_: None,
                s_05_Latest_Pick_Up_Date_TimeSet: None,
                s_06: None,
                s_06_Latest_Delivery_Date_TimeSet: None,
                s_07_PickUp_Progress: None,
                s_08_Delivery_Progress: None,
                s_20_Actual_Pickup_TimeStamp: None,
                s_21_Actual_Delivery_TimeStamp: None,
                b_handling_Instructions: None,
                v_price_Booking: 0,
                v_service_Type_2: None,
                b_status_API: None,
                v_vehicle_Type: None,
                v_customer_code: None,
                v_service_Type_ID: None,
                v_service_Type: None,
                v_serviceCode_DME: None,
                v_service_Delivery_Days_Percentage_Days_TO_PU: 0,
                v_serviceTime_End: None,
                v_serviceTime_Start: None,
                v_serviceDelivery_Days: 0,
                v_service_Delivery_Hours: 0,
                v_service_DeliveryHours_TO_PU: 0,
                x_booking_Created_With: None,
                x_manual_booked_flag: False,
                de_Email_Group_Emails: None,
                de_Email_Group_Name: None,
                de_Options: None,
                total_lines_qty_overri: 0,
                total_1_KG_weight_override: 0,
                total_Cubic_Meter_override: 0,
                booked_for_comm_communicate_via: None,
                booking_Created_For: None,
                b_order_created: order['date_created'],
                b_error_Capture: None,
                b_error_code: None,
                b_booking_Category: None,
                pu_PickUp_By_Time_Hours: 0,
                pu_PickUp_By_Time_Minutes: 0,
                pu_PickUp_Avail_Time_Hours: 0,
                pu_PickUp_Avail_Time_Minutes: 0,
                pu_PickUp_Avail_Time_Hours_DME: 0,
                pu_PickUp_Avail_Time_Minutes_DME: 0,
                pu_PickUp_By_Date_DME: None,
                pu_PickUp_By_Time_Hours_DME: 0,
                pu_PickUp_By_Time_Minutes_DME: 0,
                pu_Actual_Date: None,
                pu_Actual_PickUp_Time: None,
                de_Deliver_From_Date: None,
                de_Deliver_From_Hours: 0,
                de_Deliver_From_Minutes: 0,
                de_Deliver_By_Date: None,
                de_Deliver_By_Hours: 0,
                de_Deliver_By_Minutes: 0,
                DME_Base_Cost: 0,
                vx_Transit_Duration: 0,
                vx_freight_time: None,
                vx_price_Booking: 0,
                vx_price_Tax: 0,
                vx_price_Total_Sell_Price_Override: 0,
                vx_fp_pu_eta_time: None,
                vx_fp_del_eta_time: None,
                vx_service_Name_ID: None,
                vx_futile_Booking_Notes: None,
                z_CreatedByAccount: None,
                pu_Operting_Hours: None,
                de_Operating_Hours: None,
                z_CreatedTimestamp: timezone.now,
                z_ModifiedByAccount: None,
                z_ModifiedTimestamp: timezone.now,
                pu_PickUp_TimeSlot_TimeEnd: None,
                de_TimeSlot_TimeStart: None,
                de_TimeSlot_Time_End: None,
                de_Nospecific_Time: 0,
                de_to_TimeSlot_Date_End: None,
                rec_do_not_Invoice: 0,
                b_email_Template_Name: None,
                pu_No_specified_Time: 0,
                notes_cancel_Booking: None,
                booking_Created_For_Email: None,
                z_Notes_Bugs: None,
                DME_GST_Percentage: 0,
                x_ReadyStatus: None,
                DME_Notes: None,
                b_cli: None,
                s_04_Max_Duration_To_Delivery_Number: 0,
                b_client_MarkUp_PercentageOverRide: 0,
                z_admin_dme_invoice_number: None,
                b_dateinvoice: None,
                b_booking_tail_lift_pickup: False,
                b_booking_tail_lift_deliver: False,
                b_booking_no_operator_pickup: None,
                b_bookingNoOperatorDeliver: None,
                b_ImportedFromFile: None,
                b_email2_return_sent_numberofTimes: 0,
                b_email1_general_sent_Number_of_times: 0,
                b_email3_pickup_sent_numberOfTimes: 0,
                b_email4_futile_sent_number_of_times: 0,
                b_send_POD_eMail: False,
                b_booking_status_manual: None,
                b_booking_status_manual_DME: None,
                b_booking_statusmanual_DME_Note: None,
                client_overrided_quote: None,
                z_label_url: None,
                s_21_ActualDeliveryTimeStamp: None,
                b_client_booking_ref_num: None,
                b_client_sales_inv_num: None,
                b_client_order_num: None,
                b_client_del_note_num: None,
                b_client_w: None,
                vx_fp_order_id: None,
                z_manifest_url: None,
                z_pod_url: None,
                z_pod_signed_url: None,
                z_connote_url: None,
                z_downloaded_pod_timestam: None,
                z_downloaded_pod_sog_timestam: None,
                z_downloaded_connote_timestam: None,
                booking_api_start_TimeStam: None,
                booking_api_end_TimeStam: None,
                booking_api_try_count: 0
                z_manual_booking_set_to_confir: None,
                z_manual_booking_set_time_push_to_f: None,
                z_lock_status: False,
                z_locked_status_time: None,
                delivery_kpi_days: 0,
                delivery_days_from_booked: 0,
                delivery_actual_kpi_days: 0,
                b_status_sub_client: None,
                b_status_sub_fp: None,
                fp_store_event_date: None,
                fp_store_event_time: None,
                fp_store_event_desc: None,
                e_qty_scanned_fp_total: 0,
                dme_status_detail: None,
                dme_status_action: None,
                dme_status_linked_reference_from_fp: None,
                rpt_pod_from_file_time: None,
                rpt_proof_of_del_from_csv_time: None,
                z_status_process_notes: None,
                tally_delivered: 0,
                manifest_timestamp: None,
                inv_billing_status: None,
                inv_billing_status_note: None,
                check_pod: False,
                vx_freight_provider_carrier: None,
                fk_manifest: None,
                b_is_flagged_add_on_services: False,
                z_calculated_ETA: None,
                b_client_nam: None,
                fp_invoice_no: None,
                inv_cost_quoted: 0,
                inv_cost_actual: 0,
                inv_sell_quoted: 0,
                inv_sell_quoted_override: None,
                inv_sell_actual: 0,
                b_del_to_signed: None,
                b_del_to_signed_time: None,
                z_pushed_to_fm: False,
                b_fp_qty_delivered: 0,
                jobNumber: None,
                jobDate: None,
                vx_account_code: None,
                b_booking_project: None,
                b_project_opened: None,
                b_project_inventory_due: None,
                b_project_wh_unpack: None,
                b_project_dd_receive_dat: None,
                b_project_due_date: None,
                b_given_to_transport_date_time: None,
                fp_received_date_time: None,
                api_booking_quote: None,
                prev_dme_status_detail: None,
                dme_status_detail_updated_a: None,
                dme_status_detail_updat: None,
                delivery_booking: None,
                pu_location: None,
                de_to_location: None,
                pu_floor_number: 0,
                de_floor_number: 0,
                pu_floor_access_by: None,
                de_to_floor_access_by: None,
                de_to_sufficient_space: True,
                de_to_assembly_required: False,
                pu_no_of_assists: 0,
                de_no_of_assists: 0,
                pu_access: None,
                de_access: None,
                pu_service: None,
                de_service: None,
                booking_type: None
            }
            lines = []
            for line in order['line_items']:
                try:
                    product = wcapi.get(f"products/{line['product_id']}").json()
                except Exception as e:
                    print(f"Get Product(line) for order {order['id']} error: {e}")
                    product = None

                if product:
                    lines.append({
                        e_type_of_packaging: None,
                        e_item_type: None,
                        e_pallet_type: None,
                        e_item: None,
                        e_qty: line['quantity'],
                        e_weightUOM: 'kg',
                        e_weightPerEach: product['weight'],
                        e_dimUOM: 'cm',
                        e_dimLength: product['dimensions']['length'],
                        e_dimWidth: product['dimensions']['width'],
                        e_dimHeight: product['dimensions']['height'],
                        e_dangerousGoods: None,
                        e_insuranceValueEach: None,
                        discount_rate: None,
                        e_options1: None,
                        e_options2: None,
                        e_options3: None,
                        e_options4: None,
                        fk_service_id: None,
                        z_createdByAccount: None,
                        z_documentUploadedUser: None,
                        z_modifiedByAccount: None,
                        e_spec_clientRMA_Number: None,
                        e_spec_customerReferenceNo: None,
                        taxable: None,
                        e_Total_KG_weight: line['quantity'] * product['weight'],
                        e_1_Total_dimCubicMeter: product['dimensions']['length'] * product['dimensions']['width'] * product['dimensions']['height'],
                        client_item_reference: None,
                        total_2_cubic_mass_factor_calc: 0,
                        e_qty_awaiting_inventory: 0,
                        e_qty_collected: 0,
                        e_qty_scanned_depot: 0,
                        e_qty_delivered: 0,
                        e_qty_adjusted_delivered: 0,
                        e_qty_damaged: 0,
                        e_qty_returned: 0,
                        e_qty_shortages: 0,
                        e_qty_scanned_fp: 0,
                        z_pushed_to_fm: None,
                        is_deleted: False,
                        sscc: None,
                        picked_up_timestamp: None,
                        packed_status: None,
                        zbl_121_integer_1: None,
                        zbl_131_decimal_1: None,
                        zbl_102_text_2: None,
                        z_createdByAccount: None,
                        z_createdTimeStamp: timezone.now,
                        z_modifiedByAccount: None,
                        z_modifiedTimeStamp: timezone.now
                    })
            booking['lines'] = lines
            orders.append(booking)
    return order_list

    
def add_or_update_orders(orders):
    with mysqlcon.cursor() as cursor:
        for order in orders:
            # check if order already exists
            sql = "SELECT `id`, `b_bookingID_Visual`, `pk_booking_id`, `b_status`, `b_status_API` \
                    From `dme_bookings` \
                    WHERE `v_FPBookingNumber`=%s"
            cursor.execute(sql, (consignment_number))
            booking = cursor.fetchone()

            if booking['*'] == order['*']:
                # sql = "UPDATE `dme_bookings` \
                #     SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s, b_status=%s \
                #     WHERE `v_FPBookingNumber`=%s"
                # cursor.execute(
                #     sql,
                #     (
                #         b_del_to_signed_name,
                #         b_del_to_signed_time,
                #         datetime.datetime.now(),
                #         transit_state,
                #         dme_status,
                #         consignment_number,
                #     ),
                # )
                # mysqlcon.commit()

                # sql = "UPDATE `dme_booking_lines` \
                #     SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s, b_status=%s \
                #     WHERE `v_FPBookingNumber`=%s"
                # cursor.execute(
                #     sql,
                #     (
                #         b_del_to_signed_name,
                #         b_del_to_signed_time,
                #         datetime.datetime.now(),
                #         transit_state,
                #         dme_status,
                #         consignment_number,
                #     ),
                # )
                # mysqlcon.commit()

            else:
                # sql = "Insert `dme_bookings` \
                #     SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s, b_status=%s \
                #     WHERE `v_FPBookingNumber`=%s"
                # cursor.execute(
                #     sql,
                #     (
                #         b_del_to_signed_name,
                #         b_del_to_signed_time,
                #         datetime.datetime.now(),
                #         transit_state,
                #         dme_status,
                #         consignment_number,
                #     ),
                # )
                # mysqlcon.commit()

                # sql = "insert `dme_booking_lines` \
                #     SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s, b_status=%s \
                #     WHERE `v_FPBookingNumber`=%s"
                # cursor.execute(
                #     sql,
                #     (
                #         b_del_to_signed_name,
                #         b_del_to_signed_time,
                #         datetime.datetime.now(),
                #         transit_state,
                #         dme_status,
                #         consignment_number,
                #     ),
                # )
                # mysqlcon.commit()


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())
    time1 = time.time()

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

    # try:
    #     option = get_option(mysqlcon, "st_status_pod")

    #     if int(option["option_value"]) == 0:
    #         print("#905 - `st_status_pod` option is OFF")
    #     elif option["is_running"]:
    #         print("#905 - `st_status_pod` script is already RUNNING")
    #     else:
    #         print("#906 - `st_status_pod` option is ON")
    #         set_option(mysqlcon, "st_status_pod", True)
    #         print("#910 - Processing...")
        orders = get_orders_from_woocommerce('2021-08-01T00:00:00', '2021-08-09T00:00:00')
        add_or_update_orders(orders)

    # except Exception as e:
    #     print("Error 904:", str(e))
    \

    #     set_option(mysqlcon, "st_status_pod", False, time1)


    mysqlcon.close()
    print("#999 - Finished %s" % datetime.datetime.now())



// order data sample

{
  'id': 110467, 
  'parent_id': 0, 
  'status': 'on-hold', 
  'currency': 'AUD', 
  'version': '5.5.2', 
  'prices_include_tax': True, 
  'date_created': '2021-08-08T23:58:26', 
  'date_modified': '2021-08-08T23:59:04', 
  'discount_total': '355', 
  'discount_tax': '35', 
  'shipping_total': '0', 
  'shipping_tax': '0', 
  'cart_tax': '319', 
  'total': '3508',
  'total_tax': '319', 
  'customer_id': 0, 
  'order_key': 'wc_order_R4xxJKxuiPOET', 
  'billing': {
    'first_name': 'Kenneth', 
    'last_name': 'Lam', 
    'company': '', 
    'address_1': '80 Pringle Avenue', 
    'address_2': '', 
    'city': 'BELROSE', 
    'state': 'NSW', 
    'postcode': '2085', 
    'country': 'AU', 
    'email': 'kenneth.k.lam@live.com', 
    'phone': '0405389702'
  }, 
  'shipping': {
    'first_name': 'Kenneth', 
    'last_name': 'Lam', 
    'company': '', 
    'address_1': '80 Pringle Avenue', 
    'address_2': '', 
    'city': 'BELROSE', 
    'state': 'NSW', 
    'postcode': '2085', 
    'country': 'AU'
  }, 
  'payment_method': 'paypal', 
  'payment_method_title': 'PayPal', 
  'transaction_id': '', 
  'customer_ip_address': '159.196.170.76', 
  'customer_user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36', 
  'created_via': 'checkout', 
  'customer_note': '', 
  'date_completed': None, 
  'date_paid': None, 
  'cart_hash': '6cac378ed91756ff60bff1b5499eccf2', 
  'number': '110467', 
  'meta_data': [
    {
      'id': 2173712, 
      'key': '_billing_same_as_shipping', 
      'value': ''
    }, 
    {
      'id': 2173713, 
      'key': '_shipping_calculator', 
      'value': ''
    }, 
    {
      'id': 2173714, 
      'key': 'is_vat_exempt', 
      'value': 'no'
    }, 
    {
      'id': 2173715, 
      'key': '_wc_jilt_cart_token', 
      'value': '48d86f5d-3106-439a-9d7e-f374bb7694de'
    }, 
    {
      'id': 2173716, 
      'key': '_wfacp_report_data', 
      'value': {
        'wfacp_total': '3508', 
        'funnel_id': 0
      }
    }, 
    {
      'id': 2173717, 
      'key': 'pys_enrich_data', 
      'value': {
        'pys_landing': '', 
        'pys_source': '', 
        'pys_utm': '', 
        'pys_browser_time': ''
      }
    }, 
    {
      'id': 2173718, 
      'key': '_woofunnel_cid', 
      'value': '9029'
    }, 
    {
      'id': 2173719, 
      'key': '_xero_invoice_id', 
      'value': 'b42d3464-3ebd-4b45-8db0-fc86ef3e0ce8'
    }, 
    {
      'id': 2173720, 
      'key': '_xero_currencyrate', 
      'value': '1.0000000000'
    }, 
    {
      'id': 2173721, 
      'key': '_xero_invoice_hash', 
      'value': '802fff02c970914035d4aededb7212e358b3b678'
    }, 
    {
      'id': 2173722, 
      'key': '_wc_jilt_marketing_consent_offered', 
      'value': 'no'
    }, 
    {
      'id': 2173723, 
      'key': '_wfacp_post_id', 
      'value': '42504'
    }, 
    {
      'id': 2173724, 
      'key': '_wfacp_source', 
      'value': 'https://bathroomsalesdirect.com.au/checkout/'
    }, 
    {
      'id': 2173725, 
      'key': '_wfacp_timezone', 
      'value': 'Australia/Sydney'
    }, 
    {
      'id': 2173726, 
      'key': 'order_comments', 
      'value': ''
    }, 
    {
      'id': 2173727, 
      'key': 'pys_enrich_data_analytics', 
      'value': {
        'orders_count': 1, 
        'avg_order_value': 3189, 
        'ltv': 3189
      }
    }, 
    {
      'id': 2173728, 
      'key': '_pys_purchase_event_fired', 
      'value': '1'
    }, 
    {
      'id': 2173729, 
      'key': '_ga_tracked', 
      'value': '1'
    }, 
    {
      'id': 2173730, 
      'key': '_wfacp_report_needs_normalization', 
      'value': 'yes'
    }, 
    {
      'id': 2173734, 
      'key': '_wcct_goaldeal_sold_backup', 
      'value': {'sold': 'y'}
    }, 
    {
      'id': 2173736, 
      'key': 'wf_invoice_number', 
      'value': 'BSD110467'
    }, 
    {
      'id': 2173737, 
      'key': '_wf_invoice_date', 
      'value': '1628467106'
    }, 
    {
      'id': 2173738, 
      'key': '_new_order_email_sent', 
      'value': 'true'
    }, 
    {
      'id': 2173739, 
      'key': '_wc_jilt_placed_at', 
      'value': '1628431154'
    }
  ], 
  'line_items': [
    {
      'id': 46073, 
      'name': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold', 
      'product_id': 13050, 
      'variation_id': 0, 
      'quantity': 1, 
      'tax_class': '', 
      'subtotal': '325', 
      'subtotal_tax': '32', 
      'total': '293', 
      'total_tax': '29', 
      'taxes': [
        {
          'id': 4, 
          'total': '29.272727', 
          'subtotal': '32.454545'
        }
      ], 
      'meta_data': [
        {
          'id': 363530, 
          'key': 'product_extras', 
          'value': {
            'product_id': 13050, 
            'title': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold', 
            'groups': []
          }, 
          'display_key': 'product_extras', 
          'display_value': {
            'product_id': 13050, 
            'title': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold', 
            'groups': []
          }
        }, 
        {
          'id': 363646, 
          'key': '_WCPA_order_meta_data', 
          'value': '', 
          'display_key': '_WCPA_order_meta_data', 
          'display_value': ''
        }
      ], 
      'sku': 'STRM005BM', 
      'price': 292.727273, 
      'parent_name': None, 
      'url': 'https://bathroomsalesdirect.com.au/product/vivid-mini-pull-out-kitchen-mixer-pvd-brushed-bronze/', 
      'image_url': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/05/STRM005BM-01-e1553818564644.png'
    }, 
  ], 
  'tax_lines': [
    {
      'id': 46085, 
      'rate_code': 'TAX-1', 
      'rate_id': 4, 
      'label': 'Tax', 
      'compound': False, 
      'tax_total': '319', 
      'shipping_tax_total': '0', 
      'rate_percent': 10, 
      'meta_data': []
    }
  ], 
  'shipping_lines': [
    {
      'id': 46084, 
      'method_title': 'Free Shipping Sydney 25km', 
      'method_id': 'free_shipping', 
      'instance_id': '24', 
      'total': '0', 
      'total_tax': '0', 
      'taxes': [], 
      'meta_data': [
        {
          'id': 363636, 
          'key': 'Items', 
          'value': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold &times; 1, Ovia Milan Wall Basin Bath Mixer with 180mm Spout Brushed Gold &times; 3, Ovia Milan Shower Bath Mixer Round Brushed Gold &times; 2, Ovia Brushed Gold 2 in 1 Round Shower Station Single Hose &times; 2, Ruki Basin Mixer Brushed Nickel &times; 1, Mirage Toilet Paper Holder Brushed Nickel &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Urban Brass &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Brushed Nickel &times; 1, Ovia Milan Brushed Gold Robe Hook &times; 6, Ovia London Back to Wall Rimless Toilet &times; 1, Mercio Pani Rimless Back to Wall Toilet &times; 1', 
          'display_key': 'Items', 
          'display_value': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold &times; 1, Ovia Milan Wall Basin Bath Mixer with 180mm Spout Brushed Gold &times; 3, Ovia Milan Shower Bath Mixer Round Brushed Gold &times; 2, Ovia Brushed Gold 2 in 1 Round Shower Station Single Hose &times; 2, Ruki Basin Mixer Brushed Nickel &times; 1, Mirage Toilet Paper Holder Brushed Nickel &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Urban Brass &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Brushed Nickel &times; 1, Ovia Milan Brushed Gold Robe Hook &times; 6, Ovia London Back to Wall Rimless Toilet &times; 1, Mercio Pani Rimless Back to Wall Toilet &times; 1'
        }
      ]
    }
  ], 
  'fee_lines': [], 
  'coupon_lines': [
    {
      'id': 46086, 
      'code': 'flash10', 
      'discount': '355', 
      'discount_tax': '35', 
      'meta_data': [
        {
          'id': 363645, 
          'key': 'coupon_data', 
          'value': {
            'id': 110221, 
            'code': 'flash10', 
            'amount': '10', 
            'date_created': {
              'date': '2021-08-06 16:58:15.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'
            }, 
            'date_modified': {
              'date': '2021-08-06 16:58:15.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'  
            }, 
            'date_expires': {
              'date': '2021-08-09 00:00:00.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'
            }, 
            'discount_type': 'percent', 
            'description': '', 
            'usage_count': 64, 
            'individual_use': True, 
            'product_ids': [], 
            'excluded_product_ids': [], 
            'usage_limit': 0, 
            'usage_limit_per_user': 0, 
            'limit_usage_to_x_items': None, 
            'free_shipping': False, 
            'product_categories': [], 
            'excluded_product_categories': [], 
            'exclude_sale_items': False, 
            'minimum_amount': '', 
            'maximum_amount': '', 
            'email_restrictions': [], 
            'virtual': False, 
            'meta_data': [
              {
                'id': 2162639, 
                'key': 'rs_page_bg_color', 
                'value': ''
              }
            ]
          }, 
          'display_key': 'coupon_data', 
          'display_value': {
            'id': 110221, 
            'code': 'flash10', 
            'amount': '10', 
            'date_created': {
              'date': '2021-08-06 16:58:15.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'
            }, 
            'date_modified': {
              'date': '2021-08-06 16:58:15.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'
            }, 
            'date_expires': {
              'date': '2021-08-09 00:00:00.000000', 
              'timezone_type': 3, 
              'timezone': 'Australia/Sydney'
            }, 
            'discount_type': 'percent', 
            'description': '', 
            'usage_count': 64, 
            'individual_use': True, 
            'product_ids': [], 
            'excluded_product_ids': [], 
            'usage_limit': 0, 
            'usage_limit_per_user': 0, 
            'limit_usage_to_x_items': None, 
            'free_shipping': False, 
            'product_categories': [], 
            'excluded_product_categories': [], 
            'exclude_sale_items': False, 
            'minimum_amount': '', 
            'maximum_amount': '', 
            'email_restrictions': [], 
            'virtual': False, 
            'meta_data': [
              {
                'id': 2162639, 
                'key': 'rs_page_bg_color', 
                'value': ''
              }
            ]
          }
        }
      ]
    }
  ], 
  'refunds': [], 
  'date_created_gmt': '2021-08-08T13:58:26', 
  'date_modified_gmt': '2021-08-08T13:59:04', 
  'date_completed_gmt': None, 
  'date_paid_gmt': None, 
  'jilt': {
    'admin_url': 'https://bathroomsalesdirect.com.au/wp-admin/post.php?post=110467&action=edit', 
    'financial_status': 'pending', 
    'fulfillment_status': 'unfulfilled', 
    'requires_shipping': True, 
    'placed_at': '2021-08-08T13:59:14Z', 
    'cancelled_at': None, 
    'test': None, 
    'customer_admin_url': '', 
    'cart_token': '48d86f5d-3106-439a-9d7e-f374bb7694de', 
    'checkout_url': 'https://bathroomsalesdirect.com.au/wc-api/jilt?token=eyJjYXJ0X3Rva2VuIjoiNDhkODZmNWQtMzEwNi00MzlhLTlkN2UtZjM3NGJiNzY5NGRlIn0%3D&hash=99e5e8121508070a776b3f9a99ea32384fccf8edc1fb25f69be942d753f4689b'
  }, 
  'currency_symbol': '$', 
  '_links': {
    'self': [
      {
        'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/orders/110467'
      }
    ], 
    'collection': [
      {
        'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/orders'
      }
    ]
  }
}, 




/// product( for line data ) data sample
{
  'id': 18457, 
  'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome', 
  'slug': 'fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy', 
  'permalink': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/', 
  'date_created': '2019-08-08T22:32:41', 
  'date_created_gmt': '2019-08-08T12:32:41', 
  'date_modified': '2021-05-30T21:23:06', 
  'date_modified_gmt': '2021-05-30T11:23:06', 
  'type': 'simple', 
  'status': 'publish', 
  'featured': False, 
  'catalog_visibility': 'visible', 
  'description': '<p>[vc_row][vc_column][vc_text_separator title="KEY FEATURES" i_icon_fontawesome="fa fa-book" i_color="sky" title_align="separator_align_left" add_icon="true"][vc_column_text text_larger="no"]</p>\n<ul>\n<li>Stunning modern vintage style</li>\n<li>Swivel function</li>\n<li>Chrome finish</li>\n<li>Brass construction</li>\n<li>Quality European cartridge, 35mm</li>\n<li>Suitable for mains pressure, max. 500kpa</li>\n<li>PEX Split-proof hoses</li>\n</ul>\n<h5 data-fontsize="13" data-lineheight="19">WELS 5 Star rated, 5.5L/min<br />\nWELS Registration: T30665</h5>\n<p>[/vc_column_text][/vc_column][/vc_row][vc_row][vc_column][vc_btn title="DOWNLOAD SPECS" style="flat" shape="square" color="primary" i_icon_fontawesome="fa fa-file-pdf-o" add_icon="true" link="url:https%3A%2F%2Fwww.dropbox.com%2Fs%2Fhoaqvfcluqmk9ds%2FEleanorChrome_Mixers_MPGs.pdf%3Fdl%3D0|||"][/vc_column][/vc_row]</p>\n',
  'short_description': '', 
  'sku': '202103CC', 
  'price': '305', 
  'regular_price': '359', 
  'sale_price': '305', 
  'date_on_sale_from': None, 
  'date_on_sale_from_gmt': None, 
  'date_on_sale_to': None, 
  'date_on_sale_to_gmt': None, 
  'on_sale': True, 
  'purchasable': True, 
  'total_sales': 5, 
  'virtual': False, 
  'downloadable': False, 
  'downloads': [], 
  'download_limit': -1, 
  'download_expiry': -1, 
  'external_url': '', 
  'button_text': '', 
  'tax_status': 'taxable', 
  'tax_class': '', 
  'manage_stock': False, 
  'stock_quantity': None, 
  'backorders': 'no', 
  'backorders_allowed': False, 
  'backordered': False, 
  'low_stock_amount': None, 
  'sold_individually': False, 
  'weight': '5', 
  'dimensions': {
    'length': '30', 
    'width': '60', 
    'height': '10'
  }, 
  'shipping_required': True, 
  'shipping_taxable': True, 
  'shipping_class': '', 
  'shipping_class_id': 0, 
  'reviews_allowed': True, 
  'average_rating': '0.00', 
  'rating_count': 0, 
  'upsell_ids': [], 
  'cross_sell_ids': [], 
  'parent_id': 0, 
  'purchase_note': '', 
  'categories': [
    {
      'id': 789, 
      'name': 'Bathroom Tapware Online', 
      'slug': 
      'tapware'
    }, 
    {
      'id': 790, 
      'name': 'Basin Mixer Taps', 
      'slug': 'basin-mixers'
    }
  ], 
  'tags': [], 
  'images': [
    {
      'id': 18459, 
      'date_created': '2019-08-09T08:38:34', 
      'date_created_gmt': '2019-08-08T12:38:34', 
      'date_modified': '2019-08-09T08:38:34', 
      'date_modified_gmt': '2019-08-08T12:38:34', 
      'src': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg', 
      'name': '202103CC_1', 
      'alt': ''
    }
  ], 
  'attributes': [
    {
      'id': 1, 
      'name': 'Brand', 
      'position': 0, 
      'visible': True, 
      'variation': False, 
      'options': [
        'FIENZA'
      ]
    }, 
    {
      'id': 7, 
      'name': 'Colour', 
      'position': 1, 
      'visible': True, 
      'variation': False, 
      'options': [
        'Chrome'
      ]
    }, 
    {
      'id': 17, 
      'name': 'WELS Rating', 
      'position': 2, 
      'visible': True, 
      'variation': False, 
      'options': [
        '5 star WELS Rating'
      ]
    }, 
    {
      'id': 52, 
      'name': 'Collection', 
      'position': 3, 
      'visible': True, 
      'variation': True, 
      'options': [
        'Eleanor'
      ]
    }
  ], 
  'default_attributes': [],  
  'variations': [], 
  'grouped_products': [], 
  'menu_order': 0, 
  'price_html': '<del aria-hidden="true"><span class="woocommerce-Price-amount amount"><bdi><span class="woocommerce-Price-currencySymbol">&#36;</span>359</bdi></span></del> <ins><span class="woocommerce-Price-amount amount"><bdi><span class="woocommerce-Price-currencySymbol">&#36;</span>305</bdi></span></ins>', 
  'related_ids': [
    5090, 
    4960, 
    5085, 
    5088, 
    5102
  ], 
  'meta_data': [
    {
      'id': 273874, 
      'key': 'classic-editor-remember', 
      'value': 'classic-editor'
    }, 
    {
      'id': 273875, 
      'key': '_wcsquare_disable_sync', 
      'value': 'no'
    }, 
    {
      'id': 273876, 
      'key': '_bj_lazy_load_skip_post', 
      'value': 'false'
    }, 
    {
      'id': 273877, 
      'key': '_yoast_wpseo_primary_product_cat', 
      'value': '789'
    }, 
    {
      'id': 273878, 
      'key': 'post_sidebar', 
      'value': {
        'sidebar-1': '', 
        'sidebar-shop': '', 
        'filters-area': '',
        'sidebar-product-single': '', 
        'sidebar-my-account': '', 
        'sidebar-full-screen-menu': '', 
        'mobile-menu-widgets': '', 
        'footer-1': '', 
        'footer-2': '', 
        'footer-3': '', 
        'footer-4': '', 
        'sidebar-7633': '', 
        'sidebar-204': ''
      }
    }, 
    {
      'id': 273879, 
      'key': '_yoast_wpseo_content_score', 
      'value': '90'
    }, 
    {
      'id': 273880, 
      'key': '_square_item_image_id',
      'value': 'a1227cea-da66-492e-96ae-05c10a537404'
    }, 
    {
      'id': 273881, 
      'key': '_jetpack_related_posts_cache', 
      'value': {
        '32b0bf150bb6bd30c74ed5fafdacd61f': {
          'expires': 1627061171, 
          'payload': [
            {
              'id': 10284
            }, 
            {
              'id': 9287
            }, 
            {
              'id': 9487
            }
          ]
        }, 
        '414c5e39686b80472dfd19eb68d5cbda': {
          'expires': 1627095628, 
          'payload': [
            {
              'id': 10284
            }, 
            {
              'id': 9287
            }, 
            {
              'id': 9487
            }, 
            {
              'id': 8241
            }, 
            {
              'id': 86750
            }, 
            {
              'id': 86756
            }
          ]
        }
      }
    }, 
    {
      'id': 273882, 
      'key': 'woodmart_sguide_select', 
      'value': ''
    }, 
    {
      'id': 273883, 
      'key': 'woodmart_total_stock_quantity', 
      'value': ''
    }, 
    {
      'id': 273884, 
      'key': 'fb_product_description', 
      'value': ''
    }, 
    {
      'id': 273885, 
      'key': 'fb_visibility', 
      'value': '1'
    }, 
    {
      'id': 273886, 
      'key': '_product_360_image_gallery', 
      'value': ''
    }, 
    {
      'id': 273887, 
      'key': 'slide_template', 
      'value': 'default'
    }, 
    {
      'id': 273888, 
      'key': '_wpb_vc_js_status', 
      'value': 'true'
    }, 
    {
      'id': 273889, 
      'key': '_woodmart_product_design', 
      'value': 'inherit'
    }, 
    {
      'id': 273890, 
      'key': '_woodmart_single_product_style', 
      'value': 'default'
    }, 
    {
      'id': 273891, 
      'key': '_woodmart_thums_position', 
      'value': 'default'
    }, 
    {
      'id': 273892, 
      'key': '_woodmart_main_layout', 
      'value': 'default'
    }, 
    {
      'id': 273893, 
      'key': '_woodmart_sidebar_width', 
      'value': 'default'
    }, 
    {
      'id': 273894, 
      'key': '_woodmart_custom_sidebar', 
      'value': 'none'
    }, 
    {
      'id': 273895, 
      'key': '_woodmart_extra_content', 
      'value': '0'
    }, 
    {
      'id': 273896, 
      'key': '_woodmart_extra_position', 
      'value': 'after'
    }, 
    {
      'id': 273897, 
      'key': '_wpas_done_all', 
      'value': '1'
    }, 
    {
      'id': 273906, 
      'key': '_square_item_id', 
      'value': '7c3fe813-545a-4446-96b4-547a748e7473'
    }, 
    {
      'id': 273907, 
      'key': '_square_item_variation_id', 
      'value': 'dcb23965-bf1f-4886-961f-cf98f8f8d160'
    }, 
    {
      'id': 460431, 
      'key': 'wwpp_product_wholesale_visibility_filter', 
      'value': 'all'
    }, 
    {
      'id': 463761, 
      'key': 'wholesale_customer_have_wholesale_price_set_by_product_cat', 
      'value': 'yes'
    }, 
    {
      'id': 1100186, 
      'key': 'wholesale_customer_have_wholesale_price', 
      'value': 'yes'
    }, 
    {
      'id': 1503672, 
      'key': '_sbi_oembed_done_checking', 
      'value': '1'
    }
  ], 
  'stock_status': 'instock', 
  'wcpa_form_fields': None, 
  'yoast_head': '<!-- This site is optimized with the Yoast SEO plugin v16.8 - https://yoast.com/wordpress/plugins/seo/ -->\n<title>FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd</title>\n<!-- Admin only notice: this page does not show a meta description because it does not have one, either write it for this page specifically or go into the [SEO - Search Appearance] menu and set up a template. -->\n<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />\n<link rel="canonical" href="https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/" />\n<meta property="og:locale" content="en_US" />\n<meta property="og:type" content="article" />\n<meta property="og:title" content="FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd" />\n<meta property="og:description" content="[vc_row][vc_column][vc_text_separator title=&#8221;KEY FEATURES&#8221; i_icon_fontawesome=&#8221;fa fa-book&#8221; i_color=&#8221;sky&#8221; title_align=&#8221;separator_align_left&#8221; add_icon=&#8221;true&#8221;][vc_column_text text_larger=&#8221;no&#8221;] Stunning modern vintage style Swivel function Chrome finish Brass construction Quality" />\n<meta property="og:url" content="https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/" />\n<meta property="og:site_name" content="Bathroom Sales Direct Pty Ltd" />\n<meta property="article:publisher" content="https://www.facebook.com/bathroomsalesdirect/" />\n<meta property="article:modified_time" content="2021-05-30T11:23:06+00:00" />\n<meta property="og:image" content="https://i2.wp.com/bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg?fit=1000%2C1000&#038;ssl=1" />\n\t<meta property="og:image:width" content="1000" />\n\t<meta property="og:image:height" content="1000" />\n<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:label1" content="Est. reading time" />\n\t<meta name="twitter:data1" content="1 minute" />\n<script type="application/ld+json" class="yoast-schema-graph">{"@context":"https://schema.org","@graph":[{"@type":"WebSite","@id":"https://bathroomsalesdirect.com.au/#website","url":"https://bathroomsalesdirect.com.au/","name":"Bathroom Sales Direct Pty Ltd","description":"For all your bathroom supplies","potentialAction":[{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":"https://bathroomsalesdirect.com.au/?s={search_term_string}"},"query-input":"required name=search_term_string"}],"inLanguage":"en-US"},{"@type":"ImageObject","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage","inLanguage":"en-US","url":"https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg","contentUrl":"https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg","width":1000,"height":1000},{"@type":"WebPage","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#webpage","url":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/","name":"FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd","isPartOf":{"@id":"https://bathroomsalesdirect.com.au/#website"},"primaryImageOfPage":{"@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage"},"datePublished":"2019-08-08T12:32:41+00:00","dateModified":"2021-05-30T11:23:06+00:00","breadcrumb":{"@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb"},"inLanguage":"en-US","potentialAction":[{"@type":"ReadAction","target":["https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/"]}]},{"@type":"BreadcrumbList","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"Shop","item":"https://bathroomsalesdirect.com.au/shop_bathroom_supplies/"},{"@type":"ListItem","position":2,"name":"FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome"}]}]}</script>\n<!-- / Yoast SEO plugin. -->', 
  'yoast_head_json': {
    'title': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd', 
    'robots': {
      'index': 'index', 
      'follow': 'follow', 
      'max-snippet': 'max-snippet:-1', 
      'max-image-preview': 'max-image-preview:large', 
      'max-video-preview': 'max-video-preview:-1'
    }, 
    'canonical': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/', 
    'og_locale': 'en_US', 
    'og_type': 'article', 
    'og_title': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd', 
    'og_description': '[vc_row][vc_column][vc_text_separator title=&#8221;KEY FEATURES&#8221; i_icon_fontawesome=&#8221;fa fa-book&#8221; i_color=&#8221;sky&#8221; title_align=&#8221;separator_align_left&#8221; add_icon=&#8221;true&#8221;][vc_column_text text_larger=&#8221;no&#8221;] Stunning modern vintage style Swivel function Chrome finish Brass construction Quality', 
    'og_url': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/', 
    'og_site_name': 'Bathroom Sales Direct Pty Ltd', 
    'article_publisher': 'https://www.facebook.com/bathroomsalesdirect/', 
    'article_modified_time': '2021-05-30T11:23:06+00:00', 
    'og_image': [
      {
        'width': 1000, 
        'height': 1000, 
        'url': 'https://i2.wp.com/bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg?fit=1000%2C1000&ssl=1', 'path': '/home/bathroo3/public_html/wp-content/uploads/2019/08/202103CC_1.jpg', 
        'size': 'full', 
        'id': 18459, 
        'alt': '', 
        'pixels': 1000000, 
        'type': 'image/jpeg'
      }
    ], 
    'twitter_card': 'summary_large_image', 
    'twitter_misc': {
      'Est. reading time': '1 minute'
    }, 
    'schema': {
      '@context': 'https://schema.org', 
      '@graph': [
        {
          '@type': 'WebSite', 
          '@id': 'https://bathroomsalesdirect.com.au/#website', 
          'url': 'https://bathroomsalesdirect.com.au/', 
          'name': 'Bathroom Sales Direct Pty Ltd', 
          'description': 'For all your bathroom supplies', 
          'potentialAction': [
            {
              '@type': 'SearchAction', 
              'target': {
                '@type': 'EntryPoint', 
                'urlTemplate': 'https://bathroomsalesdirect.com.au/?s={search_term_string}'
              }, 
              'query-input': 'required name=search_term_string'
            }
          ], 
          'inLanguage': 'en-US'
        }, 
        {
          '@type': 'ImageObject', 
          '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage', 
          'inLanguage': 'en-US', 
          'url': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg', 
          'contentUrl': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg', 
          'width': 1000, 
          'height': 1000
        }, 
        {
          '@type': 'WebPage', 
          '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#webpage', 
          'url': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/', 
          'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd', 
          'isPartOf': {
            '@id': 'https://bathroomsalesdirect.com.au/#website'
          }, 
          'primaryImageOfPage': {
            '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage'
          }, 
          'datePublished': '2019-08-08T12:32:41+00:00', 
          'dateModified': '2021-05-30T11:23:06+00:00', 
          'breadcrumb': {
            '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb'
          }, 
          'inLanguage': 'en-US', 
          'potentialAction': [
            {
              '@type': 'ReadAction', 
              'target': [
                'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/'
              ]
            }
          ]
        },
        {
          '@type': 'BreadcrumbList', 
          '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb', 
          'itemListElement': [
            {
              '@type': 'ListItem', 
              'position': 1, 
              'name': 'Shop', 
              'item': 'https://bathroomsalesdirect.com.au/shop_bathroom_supplies/'
            }, 
            {
              '@type': 'ListItem', 
              'position': 2, 
              'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome'
            }
          ]
        }
      ]
    }
  }, 
  '_links': {
    'self': [
      {
        'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/products/18457'
      }
    ], 
    'collection': [
      {
        'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/products'
      }
    ]
  }
}
