# Python 3.7.0

import sys, time
import os
import uuid
from datetime import datetime, timedelta
import pymysql, pymysql.cursors
import shutil
import json
import requests
import traceback

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option

from woocommerce import API

wcapi = API(
    url="https://bathroomsalesdirect.com.au/",  # Your store URL
    consumer_key="ck_b805f1858e763af3f27e5638f80e06f924ac94b1",  # Your consumer key
    consumer_secret="cs_8b52746e7285a2cbaee34046be2e5eadb09884f2",  # Your consumer secret
    wp_api=True,  # Enable the WP REST API integration
    version="wc/v3",  # WooCommerce WP REST API version
    query_string_auth=True
)


def get_token():
    # BSD user_01 credential
    USERNAME = "bsd_user_01"
    PASSWORD = "r)VNr9dK?MLYn35t"

    url = API_URL + "/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def get_orders_from_woocommerce(from_date, to_date, status):
    print(f"params - from_date: {from_date}, to_date: {to_date}, status: {status}")

    try:
        url = f"orders?"
        url += "per_page=10"
        url += f"&status={status}"
        url += "&orderby=id"
        url += "&order=desc"
        # url += "&exclude=[118368,118361,118359,118358,118357,118356,118355,118354,118353,118352,118351,118350,118349,118348,118346,118345,118341,118369,118338,118337,118335,118334,118333,118332,118326,118325,118324,118364,118360,118347,118339,118322,118321,118320,118318,118317,118314,118313,118312,118311,118307,118306,118305,118304,118303,118302,118301,118299,118298,118297,118296,118295,118293,118292,118291,118290,118289,118288,118287,118284,118283,118282,118281,118280,118279,118278,118277,118276,118265,118264,118262,118257,118294,118323,118258]"

        if from_date:
            url += f"&after={from_date}"

        if to_date:
            url += f"&before={to_date}"

        print(f"url - {url}")
        order_list = wcapi.get(url).json()

        if 'code' in order_list and order_list['code'] == 'woocommerce_rest_cannot_view':
            print(f"Message from WooCommerce: {order_list['message']}")
            return []

        return order_list
    except Exception as e:
        print(f"Get orders error: {e}")
        return []


def get_product_from_woocommerce(product_id):
    try:
        product = wcapi.get(f"products/{product_id}").json()
        return product
    except Exception as e:
        print(f"Get product error: {e}")
        return None


def add_or_update_orders():
    orders = []
    from_ts = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")
    to_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # from_ts = None
    # to_ts = None
    # orders = get_orders_from_woocommerce(from_ts, to_ts, 'processing')
    # print(f"@001 [GET ORDER] Status: 'processing', Cnt: {len(orders)}")
    orders += get_orders_from_woocommerce(from_ts, to_ts, 'on-hold')
    print(f"@002 [GET ORDER] Status: 'on-hold', Cnt: {len(orders)}")

    if len(orders) == 0:
        print(f"@003 [GET ORDER] No orders!")
        return

    print(
        f"@100 [GET ORDER] from_ts: {from_ts}, to_ts: {to_ts}, order_cnt: {len(orders)}"
    )
    token = get_token()

    for order in orders:
        print(
            f"@101 [ORDER] orderId: {order['id']}, Order Status: {order['status']}, product_cnt: {len(order['line_items'])}"
        )

        # booking = {
        #     "pk_header_id": str(uuid.uuid4()),
        #     "b_client_warehouse_code": "BSD_MERRYLANDS",
        #     "b_000_1_b_clientReference_RA_Numbers": order["order_key"],
        #     "b_001_b_freight_provider": "",
        #     "b_002_b_vehicle_type": "",
        #     "b_003_b_service_name": "",
        #     "b_005_b_created_for": "Bathroom Sales Direct",
        #     "b_006_b_created_for_email": "info@bathroomsalesdirect.com.au",
        #     "b_007_b_ready_status": "Available From",
        #     "b_008_b_category": "Standard Sales",
        #     "b_009_b_priority": "Standard",
        #     "b_012_b_driver_bring_connote": 0,
        #     "b_013_b_package_job": 0,
        #     "b_016_b_pu_instructions_address": "",
        #     "b_019_b_pu_tail_lift": 0,
        #     "b_021_b_pu_avail_from_date": order["date_modified"][:10],
        #     "b_022_b_pu_avail_from_time_hour": 8,
        #     "b_023_b_pu_avail_from_time_minute": 0,
        #     "b_027_b_pu_address_type": "Business",
        #     "b_028_b_pu_company": "Bathroom Sales Direct",
        #     "b_029_b_pu_address_street_1": "118 Merrylands Road",
        #     "b_030_b_pu_address_street_2": "",
        #     "b_031_b_pu_address_state": "NSW",
        #     "b_032_b_pu_address_suburb": "Merrylands",
        #     "b_033_b_pu_address_postalcode": "2160",
        #     "b_034_b_pu_address_country": "Australia",
        #     "b_035_b_pu_contact_full_name": "Bathroom Sales Direct",
        #     "b_037_b_pu_email": "info@bathroomsalesdirect.com.au",
        #     "b_038_b_pu_phone_main": "0296816914",
        #     "b_040_b_pu_communicate_via": "Email",
        #     "b_041_b_del_tail_lift": 0,
        #     "b_042_b_del_num_operators": 0,
        #     "b_043_b_del_instructions_contact": "",
        #     "b_044_b_del_instructions_address": "",
        #     "b_053_b_del_address_type": "Residential",
        #     "b_054_b_del_company": order["shipping"]["first_name"]
        #     + order["shipping"]["last_name"],
        #     "b_055_b_del_address_street_1": order["shipping"]["address_1"],
        #     "b_056_b_del_address_street_2": order["shipping"]["address_2"],
        #     "b_057_b_del_address_state": order["shipping"]["state"],
        #     "b_058_b_del_address_suburb": order["shipping"]["city"],
        #     "b_059_b_del_address_postalcode": order["shipping"]["postcode"],
        #     "b_060_b_del_address_country": "Australia",
        #     "b_061_b_del_contact_full_name": order["shipping"]["first_name"]
        #     + order["shipping"]["last_name"],
        #     "b_063_b_del_email": "",
        #     "b_064_b_del_phone_main": "",
        #     "b_066_b_del_communicate_via": "Email",
        #     "b_client_order_num": order["id"],
        # }

        # booking_lines = []
        # for line in order["line_items"]:
        #     print(f"@103 [PRODUCT] productId: {line['product_id']}")
        #     product = get_product_from_woocommerce(line["product_id"])

        #     if product:
        #         booking_lines.append(
        #             {
        #                 "booking_line": {
        #                     "l_009_weight_per_each": product["weight"],
        #                     "l_003_item": product["name"],
        #                     "l_004_dim_UOM": "cm",
        #                     "l_002_qty": line["quantity"],
        #                     "l_001_type_of_packaging": "Carton",
        #                     "l_005_dim_length": product["dimensions"]["length"],
        #                     "l_006_dim_width": product["dimensions"]["width"],
        #                     "l_007_dim_height": product["dimensions"]["height"],
        #                     "l_008_weight_UOM": "kg",
        #                 }
        #             }
        #         )

        # data = {"booking": booking, "booking_lines": booking_lines}

        # url = API_URL + "/boks/"
        # headers = {"Authorization": f"JWT {token}"}
        # response = requests.post(url, params={}, json=data, headers=headers)
        # response0 = response.content.decode("utf8")
        # data0 = json.loads(response0)

        # print("@901 - Result: ", data0)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.now())
    time1 = time.time()

    try:
        option = get_option(mysqlcon, "bsd_woocommerce")

        if int(option["option_value"]) == 0:
            print("#905 - `bsd_woocommerce` option is OFF")
        elif option["is_running"]:
            print("#905 - `bsd_woocommerce` script is already RUNNING")
        else:
            print("#906 - `bsd_woocommerce` option is ON")
            set_option(mysqlcon, "bsd_woocommerce", True)
            print("#910 - Processing...")
            add_or_update_orders()
            set_option(mysqlcon, "bsd_woocommerce", False, time1)
    except Exception as e:
        print(f"@000 traceback: {traceback.format_exc()}")
        print("Error 904:", str(e))
        set_option(mysqlcon, "bsd_woocommerce", False, time1)

        # set_option(mysqlcon, "st_status_pod", False, time1)
    print("#999 - Finished %s\n\n\n" % datetime.now())


# // order data sample

# {
#   'id': 110467,
#   'parent_id': 0,
#   'status': 'on-hold',
#   'currency': 'AUD',
#   'version': '5.5.2',
#   'prices_include_tax': True,
#   'date_created': '2021-08-08T23:58:26',
#   'date_modified': '2021-08-08T23:59:04',
#   'discount_total': '355',
#   'discount_tax': '35',
#   'shipping_total': '0',
#   'shipping_tax': '0',
#   'cart_tax': '319',
#   'total': '3508',
#   'total_tax': '319',
#   'customer_id': 0,
#   'order_key': 'wc_order_R4xxJKxuiPOET',
#   'billing': {
#     'first_name': 'Kenneth',
#     'last_name': 'Lam',
#     'company': '',
#     'address_1': '80 Pringle Avenue',
#     'address_2': '',
#     'city': 'BELROSE',
#     'state': 'NSW',
#     'postcode': '2085',
#     'country': 'AU',
#     'email': 'kenneth.k.lam@live.com',
#     'phone': '0405389702'
#   },
#   'shipping': {
#     'first_name': 'Kenneth',
#     'last_name': 'Lam',
#     'company': '',
#     'address_1': '80 Pringle Avenue',
#     'address_2': '',
#     'city': 'BELROSE',
#     'state': 'NSW',
#     'postcode': '2085',
#     'country': 'AU'
#   },
#   'payment_method': 'paypal',
#   'payment_method_title': 'PayPal',
#   'transaction_id': '',
#   'customer_ip_address': '159.196.170.76',
#   'customer_user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
#   'created_via': 'checkout',
#   'customer_note': '',
#   'date_completed': None,
#   'date_paid': None,
#   'cart_hash': '6cac378ed91756ff60bff1b5499eccf2',
#   'number': '110467',
#   'meta_data': [
#     {
#       'id': 2173712,
#       'key': '_billing_same_as_shipping',
#       'value': ''
#     },
#     {
#       'id': 2173713,
#       'key': '_shipping_calculator',
#       'value': ''
#     },
#     {
#       'id': 2173714,
#       'key': 'is_vat_exempt',
#       'value': 'no'
#     },
#     {
#       'id': 2173715,
#       'key': '_wc_jilt_cart_token',
#       'value': '48d86f5d-3106-439a-9d7e-f374bb7694de'
#     },
#     {
#       'id': 2173716,
#       'key': '_wfacp_report_data',
#       'value': {
#         'wfacp_total': '3508',
#         'funnel_id': 0
#       }
#     },
#     {
#       'id': 2173717,
#       'key': 'pys_enrich_data',
#       'value': {
#         'pys_landing': '',
#         'pys_source': '',
#         'pys_utm': '',
#         'pys_browser_time': ''
#       }
#     },
#     {
#       'id': 2173718,
#       'key': '_woofunnel_cid',
#       'value': '9029'
#     },
#     {
#       'id': 2173719,
#       'key': '_xero_invoice_id',
#       'value': 'b42d3464-3ebd-4b45-8db0-fc86ef3e0ce8'
#     },
#     {
#       'id': 2173720,
#       'key': '_xero_currencyrate',
#       'value': '1.0000000000'
#     },
#     {
#       'id': 2173721,
#       'key': '_xero_invoice_hash',
#       'value': '802fff02c970914035d4aededb7212e358b3b678'
#     },
#     {
#       'id': 2173722,
#       'key': '_wc_jilt_marketing_consent_offered',
#       'value': 'no'
#     },
#     {
#       'id': 2173723,
#       'key': '_wfacp_post_id',
#       'value': '42504'
#     },
#     {
#       'id': 2173724,
#       'key': '_wfacp_source',
#       'value': 'https://bathroomsalesdirect.com.au/checkout/'
#     },
#     {
#       'id': 2173725,
#       'key': '_wfacp_timezone',
#       'value': 'Australia/Sydney'
#     },
#     {
#       'id': 2173726,
#       'key': 'order_comments',
#       'value': ''
#     },
#     {
#       'id': 2173727,
#       'key': 'pys_enrich_data_analytics',
#       'value': {
#         'orders_count': 1,
#         'avg_order_value': 3189,
#         'ltv': 3189
#       }
#     },
#     {
#       'id': 2173728,
#       'key': '_pys_purchase_event_fired',
#       'value': '1'
#     },
#     {
#       'id': 2173729,
#       'key': '_ga_tracked',
#       'value': '1'
#     },
#     {
#       'id': 2173730,
#       'key': '_wfacp_report_needs_normalization',
#       'value': 'yes'
#     },
#     {
#       'id': 2173734,
#       'key': '_wcct_goaldeal_sold_backup',
#       'value': {'sold': 'y'}
#     },
#     {
#       'id': 2173736,
#       'key': 'wf_invoice_number',
#       'value': 'BSD110467'
#     },
#     {
#       'id': 2173737,
#       'key': '_wf_invoice_date',
#       'value': '1628467106'
#     },
#     {
#       'id': 2173738,
#       'key': '_new_order_email_sent',
#       'value': 'true'
#     },
#     {
#       'id': 2173739,
#       'key': '_wc_jilt_placed_at',
#       'value': '1628431154'
#     }
#   ],
#   'line_items': [
#     {
#       'id': 46073,
#       'name': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold',
#       'product_id': 13050,
#       'variation_id': 0,
#       'quantity': 1,
#       'tax_class': '',
#       'subtotal': '325',
#       'subtotal_tax': '32',
#       'total': '293',
#       'total_tax': '29',
#       'taxes': [
#         {
#           'id': 4,
#           'total': '29.272727',
#           'subtotal': '32.454545'
#         }
#       ],
#       'meta_data': [
#         {
#           'id': 363530,
#           'key': 'product_extras',
#           'value': {
#             'product_id': 13050,
#             'title': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold',
#             'groups': []
#           },
#           'display_key': 'product_extras',
#           'display_value': {
#             'product_id': 13050,
#             'title': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold',
#             'groups': []
#           }
#         },
#         {
#           'id': 363646,
#           'key': '_WCPA_order_meta_data',
#           'value': '',
#           'display_key': '_WCPA_order_meta_data',
#           'display_value': ''
#         }
#       ],
#       'sku': 'STRM005BM',
#       'price': 292.727273,
#       'parent_name': None,
#       'url': 'https://bathroomsalesdirect.com.au/product/vivid-mini-pull-out-kitchen-mixer-pvd-brushed-bronze/',
#       'image_url': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/05/STRM005BM-01-e1553818564644.png'
#     },
#   ],
#   'tax_lines': [
#     {
#       'id': 46085,
#       'rate_code': 'TAX-1',
#       'rate_id': 4,
#       'label': 'Tax',
#       'compound': False,
#       'tax_total': '319',
#       'shipping_tax_total': '0',
#       'rate_percent': 10,
#       'meta_data': []
#     }
#   ],
#   'shipping_lines': [
#     {
#       'id': 46084,
#       'method_title': 'Free Shipping Sydney 25km',
#       'method_id': 'free_shipping',
#       'instance_id': '24',
#       'total': '0',
#       'total_tax': '0',
#       'taxes': [],
#       'meta_data': [
#         {
#           'id': 363636,
#           'key': 'Items',
#           'value': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold &times; 1, Ovia Milan Wall Basin Bath Mixer with 180mm Spout Brushed Gold &times; 3, Ovia Milan Shower Bath Mixer Round Brushed Gold &times; 2, Ovia Brushed Gold 2 in 1 Round Shower Station Single Hose &times; 2, Ruki Basin Mixer Brushed Nickel &times; 1, Mirage Toilet Paper Holder Brushed Nickel &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Urban Brass &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Brushed Nickel &times; 1, Ovia Milan Brushed Gold Robe Hook &times; 6, Ovia London Back to Wall Rimless Toilet &times; 1, Mercio Pani Rimless Back to Wall Toilet &times; 1',
#           'display_key': 'Items',
#           'display_value': 'Star Mini Pull Out Kitchen Mixer Brushed Bronze Gold &times; 1, Ovia Milan Wall Basin Bath Mixer with 180mm Spout Brushed Gold &times; 3, Ovia Milan Shower Bath Mixer Round Brushed Gold &times; 2, Ovia Brushed Gold 2 in 1 Round Shower Station Single Hose &times; 2, Ruki Basin Mixer Brushed Nickel &times; 1, Mirage Toilet Paper Holder Brushed Nickel &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Urban Brass &times; 2, Fienza KAYA Hand Towel Rail/Roll Holder Brushed Nickel &times; 1, Ovia Milan Brushed Gold Robe Hook &times; 6, Ovia London Back to Wall Rimless Toilet &times; 1, Mercio Pani Rimless Back to Wall Toilet &times; 1'
#         }
#       ]
#     }
#   ],
#   'fee_lines': [],
#   'coupon_lines': [
#     {
#       'id': 46086,
#       'code': 'flash10',
#       'discount': '355',
#       'discount_tax': '35',
#       'meta_data': [
#         {
#           'id': 363645,
#           'key': 'coupon_data',
#           'value': {
#             'id': 110221,
#             'code': 'flash10',
#             'amount': '10',
#             'date_created': {
#               'date': '2021-08-06 16:58:15.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'date_modified': {
#               'date': '2021-08-06 16:58:15.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'date_expires': {
#               'date': '2021-08-09 00:00:00.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'discount_type': 'percent',
#             'description': '',
#             'usage_count': 64,
#             'individual_use': True,
#             'product_ids': [],
#             'excluded_product_ids': [],
#             'usage_limit': 0,
#             'usage_limit_per_user': 0,
#             'limit_usage_to_x_items': None,
#             'free_shipping': False,
#             'product_categories': [],
#             'excluded_product_categories': [],
#             'exclude_sale_items': False,
#             'minimum_amount': '',
#             'maximum_amount': '',
#             'email_restrictions': [],
#             'virtual': False,
#             'meta_data': [
#               {
#                 'id': 2162639,
#                 'key': 'rs_page_bg_color',
#                 'value': ''
#               }
#             ]
#           },
#           'display_key': 'coupon_data',
#           'display_value': {
#             'id': 110221,
#             'code': 'flash10',
#             'amount': '10',
#             'date_created': {
#               'date': '2021-08-06 16:58:15.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'date_modified': {
#               'date': '2021-08-06 16:58:15.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'date_expires': {
#               'date': '2021-08-09 00:00:00.000000',
#               'timezone_type': 3,
#               'timezone': 'Australia/Sydney'
#             },
#             'discount_type': 'percent',
#             'description': '',
#             'usage_count': 64,
#             'individual_use': True,
#             'product_ids': [],
#             'excluded_product_ids': [],
#             'usage_limit': 0,
#             'usage_limit_per_user': 0,
#             'limit_usage_to_x_items': None,
#             'free_shipping': False,
#             'product_categories': [],
#             'excluded_product_categories': [],
#             'exclude_sale_items': False,
#             'minimum_amount': '',
#             'maximum_amount': '',
#             'email_restrictions': [],
#             'virtual': False,
#             'meta_data': [
#               {
#                 'id': 2162639,
#                 'key': 'rs_page_bg_color',
#                 'value': ''
#               }
#             ]
#           }
#         }
#       ]
#     }
#   ],
#   'refunds': [],
#   'date_created_gmt': '2021-08-08T13:58:26',
#   'date_modified_gmt': '2021-08-08T13:59:04',
#   'date_completed_gmt': None,
#   'date_paid_gmt': None,
#   'jilt': {
#     'admin_url': 'https://bathroomsalesdirect.com.au/wp-admin/post.php?post=110467&action=edit',
#     'financial_status': 'pending',
#     'fulfillment_status': 'unfulfilled',
#     'requires_shipping': True,
#     'placed_at': '2021-08-08T13:59:14Z',
#     'cancelled_at': None,
#     'test': None,
#     'customer_admin_url': '',
#     'cart_token': '48d86f5d-3106-439a-9d7e-f374bb7694de',
#     'checkout_url': 'https://bathroomsalesdirect.com.au/wc-api/jilt?token=eyJjYXJ0X3Rva2VuIjoiNDhkODZmNWQtMzEwNi00MzlhLTlkN2UtZjM3NGJiNzY5NGRlIn0%3D&hash=99e5e8121508070a776b3f9a99ea32384fccf8edc1fb25f69be942d753f4689b'
#   },
#   'currency_symbol': '$',
#   '_links': {
#     'self': [
#       {
#         'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/orders/110467'
#       }
#     ],
#     'collection': [
#       {
#         'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/orders'
#       }
#     ]
#   }
# },


# /// product( for line data ) data sample
# {
#   'id': 18457,
#   'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome',
#   'slug': 'fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy',
#   'permalink': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/',
#   'date_created': '2019-08-08T22:32:41',
#   'date_created_gmt': '2019-08-08T12:32:41',
#   'date_modified': '2021-05-30T21:23:06',
#   'date_modified_gmt': '2021-05-30T11:23:06',
#   'type': 'simple',
#   'status': 'publish',
#   'featured': False,
#   'catalog_visibility': 'visible',
#   'description': '<p>[vc_row][vc_column][vc_text_separator title="KEY FEATURES" i_icon_fontawesome="fa fa-book" i_color="sky" title_align="separator_align_left" add_icon="true"][vc_column_text text_larger="no"]</p>\n<ul>\n<li>Stunning modern vintage style</li>\n<li>Swivel function</li>\n<li>Chrome finish</li>\n<li>Brass construction</li>\n<li>Quality European cartridge, 35mm</li>\n<li>Suitable for mains pressure, max. 500kpa</li>\n<li>PEX Split-proof hoses</li>\n</ul>\n<h5 data-fontsize="13" data-lineheight="19">WELS 5 Star rated, 5.5L/min<br />\nWELS Registration: T30665</h5>\n<p>[/vc_column_text][/vc_column][/vc_row][vc_row][vc_column][vc_btn title="DOWNLOAD SPECS" style="flat" shape="square" color="primary" i_icon_fontawesome="fa fa-file-pdf-o" add_icon="true" link="url:https%3A%2F%2Fwww.dropbox.com%2Fs%2Fhoaqvfcluqmk9ds%2FEleanorChrome_Mixers_MPGs.pdf%3Fdl%3D0|||"][/vc_column][/vc_row]</p>\n',
#   'short_description': '',
#   'sku': '202103CC',
#   'price': '305',
#   'regular_price': '359',
#   'sale_price': '305',
#   'date_on_sale_from': None,
#   'date_on_sale_from_gmt': None,
#   'date_on_sale_to': None,
#   'date_on_sale_to_gmt': None,
#   'on_sale': True,
#   'purchasable': True,
#   'total_sales': 5,
#   'virtual': False,
#   'downloadable': False,
#   'downloads': [],
#   'download_limit': -1,
#   'download_expiry': -1,
#   'external_url': '',
#   'button_text': '',
#   'tax_status': 'taxable',
#   'tax_class': '',
#   'manage_stock': False,
#   'stock_quantity': None,
#   'backorders': 'no',
#   'backorders_allowed': False,
#   'backordered': False,
#   'low_stock_amount': None,
#   'sold_individually': False,
#   'weight': '5',
#   'dimensions': {
#     'length': '30',
#     'width': '60',
#     'height': '10'
#   },
#   'shipping_required': True,
#   'shipping_taxable': True,
#   'shipping_class': '',
#   'shipping_class_id': 0,
#   'reviews_allowed': True,
#   'average_rating': '0.00',
#   'rating_count': 0,
#   'upsell_ids': [],
#   'cross_sell_ids': [],
#   'parent_id': 0,
#   'purchase_note': '',
#   'categories': [
#     {
#       'id': 789,
#       'name': 'Bathroom Tapware Online',
#       'slug':
#       'tapware'
#     },
#     {
#       'id': 790,
#       'name': 'Basin Mixer Taps',
#       'slug': 'basin-mixers'
#     }
#   ],
#   'tags': [],
#   'images': [
#     {
#       'id': 18459,
#       'date_created': '2019-08-09T08:38:34',
#       'date_created_gmt': '2019-08-08T12:38:34',
#       'date_modified': '2019-08-09T08:38:34',
#       'date_modified_gmt': '2019-08-08T12:38:34',
#       'src': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg',
#       'name': '202103CC_1',
#       'alt': ''
#     }
#   ],
#   'attributes': [
#     {
#       'id': 1,
#       'name': 'Brand',
#       'position': 0,
#       'visible': True,
#       'variation': False,
#       'options': [
#         'FIENZA'
#       ]
#     },
#     {
#       'id': 7,
#       'name': 'Colour',
#       'position': 1,
#       'visible': True,
#       'variation': False,
#       'options': [
#         'Chrome'
#       ]
#     },
#     {
#       'id': 17,
#       'name': 'WELS Rating',
#       'position': 2,
#       'visible': True,
#       'variation': False,
#       'options': [
#         '5 star WELS Rating'
#       ]
#     },
#     {
#       'id': 52,
#       'name': 'Collection',
#       'position': 3,
#       'visible': True,
#       'variation': True,
#       'options': [
#         'Eleanor'
#       ]
#     }
#   ],
#   'default_attributes': [],
#   'variations': [],
#   'grouped_products': [],
#   'menu_order': 0,
#   'price_html': '<del aria-hidden="true"><span class="woocommerce-Price-amount amount"><bdi><span class="woocommerce-Price-currencySymbol">&#36;</span>359</bdi></span></del> <ins><span class="woocommerce-Price-amount amount"><bdi><span class="woocommerce-Price-currencySymbol">&#36;</span>305</bdi></span></ins>',
#   'related_ids': [
#     5090,
#     4960,
#     5085,
#     5088,
#     5102
#   ],
#   'meta_data': [
#     {
#       'id': 273874,
#       'key': 'classic-editor-remember',
#       'value': 'classic-editor'
#     },
#     {
#       'id': 273875,
#       'key': '_wcsquare_disable_sync',
#       'value': 'no'
#     },
#     {
#       'id': 273876,
#       'key': '_bj_lazy_load_skip_post',
#       'value': 'false'
#     },
#     {
#       'id': 273877,
#       'key': '_yoast_wpseo_primary_product_cat',
#       'value': '789'
#     },
#     {
#       'id': 273878,
#       'key': 'post_sidebar',
#       'value': {
#         'sidebar-1': '',
#         'sidebar-shop': '',
#         'filters-area': '',
#         'sidebar-product-single': '',
#         'sidebar-my-account': '',
#         'sidebar-full-screen-menu': '',
#         'mobile-menu-widgets': '',
#         'footer-1': '',
#         'footer-2': '',
#         'footer-3': '',
#         'footer-4': '',
#         'sidebar-7633': '',
#         'sidebar-204': ''
#       }
#     },
#     {
#       'id': 273879,
#       'key': '_yoast_wpseo_content_score',
#       'value': '90'
#     },
#     {
#       'id': 273880,
#       'key': '_square_item_image_id',
#       'value': 'a1227cea-da66-492e-96ae-05c10a537404'
#     },
#     {
#       'id': 273881,
#       'key': '_jetpack_related_posts_cache',
#       'value': {
#         '32b0bf150bb6bd30c74ed5fafdacd61f': {
#           'expires': 1627061171,
#           'payload': [
#             {
#               'id': 10284
#             },
#             {
#               'id': 9287
#             },
#             {
#               'id': 9487
#             }
#           ]
#         },
#         '414c5e39686b80472dfd19eb68d5cbda': {
#           'expires': 1627095628,
#           'payload': [
#             {
#               'id': 10284
#             },
#             {
#               'id': 9287
#             },
#             {
#               'id': 9487
#             },
#             {
#               'id': 8241
#             },
#             {
#               'id': 86750
#             },
#             {
#               'id': 86756
#             }
#           ]
#         }
#       }
#     },
#     {
#       'id': 273882,
#       'key': 'woodmart_sguide_select',
#       'value': ''
#     },
#     {
#       'id': 273883,
#       'key': 'woodmart_total_stock_quantity',
#       'value': ''
#     },
#     {
#       'id': 273884,
#       'key': 'fb_product_description',
#       'value': ''
#     },
#     {
#       'id': 273885,
#       'key': 'fb_visibility',
#       'value': '1'
#     },
#     {
#       'id': 273886,
#       'key': '_product_360_image_gallery',
#       'value': ''
#     },
#     {
#       'id': 273887,
#       'key': 'slide_template',
#       'value': 'default'
#     },
#     {
#       'id': 273888,
#       'key': '_wpb_vc_js_status',
#       'value': 'true'
#     },
#     {
#       'id': 273889,
#       'key': '_woodmart_product_design',
#       'value': 'inherit'
#     },
#     {
#       'id': 273890,
#       'key': '_woodmart_single_product_style',
#       'value': 'default'
#     },
#     {
#       'id': 273891,
#       'key': '_woodmart_thums_position',
#       'value': 'default'
#     },
#     {
#       'id': 273892,
#       'key': '_woodmart_main_layout',
#       'value': 'default'
#     },
#     {
#       'id': 273893,
#       'key': '_woodmart_sidebar_width',
#       'value': 'default'
#     },
#     {
#       'id': 273894,
#       'key': '_woodmart_custom_sidebar',
#       'value': 'none'
#     },
#     {
#       'id': 273895,
#       'key': '_woodmart_extra_content',
#       'value': '0'
#     },
#     {
#       'id': 273896,
#       'key': '_woodmart_extra_position',
#       'value': 'after'
#     },
#     {
#       'id': 273897,
#       'key': '_wpas_done_all',
#       'value': '1'
#     },
#     {
#       'id': 273906,
#       'key': '_square_item_id',
#       'value': '7c3fe813-545a-4446-96b4-547a748e7473'
#     },
#     {
#       'id': 273907,
#       'key': '_square_item_variation_id',
#       'value': 'dcb23965-bf1f-4886-961f-cf98f8f8d160'
#     },
#     {
#       'id': 460431,
#       'key': 'wwpp_product_wholesale_visibility_filter',
#       'value': 'all'
#     },
#     {
#       'id': 463761,
#       'key': 'wholesale_customer_have_wholesale_price_set_by_product_cat',
#       'value': 'yes'
#     },
#     {
#       'id': 1100186,
#       'key': 'wholesale_customer_have_wholesale_price',
#       'value': 'yes'
#     },
#     {
#       'id': 1503672,
#       'key': '_sbi_oembed_done_checking',
#       'value': '1'
#     }
#   ],
#   'stock_status': 'instock',
#   'wcpa_form_fields': None,
#   'yoast_head': '<!-- This site is optimized with the Yoast SEO plugin v16.8 - https://yoast.com/wordpress/plugins/seo/ -->\n<title>FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd</title>\n<!-- Admin only notice: this page does not show a meta description because it does not have one, either write it for this page specifically or go into the [SEO - Search Appearance] menu and set up a template. -->\n<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />\n<link rel="canonical" href="https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/" />\n<meta property="og:locale" content="en_US" />\n<meta property="og:type" content="article" />\n<meta property="og:title" content="FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd" />\n<meta property="og:description" content="[vc_row][vc_column][vc_text_separator title=&#8221;KEY FEATURES&#8221; i_icon_fontawesome=&#8221;fa fa-book&#8221; i_color=&#8221;sky&#8221; title_align=&#8221;separator_align_left&#8221; add_icon=&#8221;true&#8221;][vc_column_text text_larger=&#8221;no&#8221;] Stunning modern vintage style Swivel function Chrome finish Brass construction Quality" />\n<meta property="og:url" content="https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/" />\n<meta property="og:site_name" content="Bathroom Sales Direct Pty Ltd" />\n<meta property="article:publisher" content="https://www.facebook.com/bathroomsalesdirect/" />\n<meta property="article:modified_time" content="2021-05-30T11:23:06+00:00" />\n<meta property="og:image" content="https://i2.wp.com/bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg?fit=1000%2C1000&#038;ssl=1" />\n\t<meta property="og:image:width" content="1000" />\n\t<meta property="og:image:height" content="1000" />\n<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:label1" content="Est. reading time" />\n\t<meta name="twitter:data1" content="1 minute" />\n<script type="application/ld+json" class="yoast-schema-graph">{"@context":"https://schema.org","@graph":[{"@type":"WebSite","@id":"https://bathroomsalesdirect.com.au/#website","url":"https://bathroomsalesdirect.com.au/","name":"Bathroom Sales Direct Pty Ltd","description":"For all your bathroom supplies","potentialAction":[{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":"https://bathroomsalesdirect.com.au/?s={search_term_string}"},"query-input":"required name=search_term_string"}],"inLanguage":"en-US"},{"@type":"ImageObject","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage","inLanguage":"en-US","url":"https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg","contentUrl":"https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg","width":1000,"height":1000},{"@type":"WebPage","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#webpage","url":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/","name":"FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd","isPartOf":{"@id":"https://bathroomsalesdirect.com.au/#website"},"primaryImageOfPage":{"@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage"},"datePublished":"2019-08-08T12:32:41+00:00","dateModified":"2021-05-30T11:23:06+00:00","breadcrumb":{"@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb"},"inLanguage":"en-US","potentialAction":[{"@type":"ReadAction","target":["https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/"]}]},{"@type":"BreadcrumbList","@id":"https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"Shop","item":"https://bathroomsalesdirect.com.au/shop_bathroom_supplies/"},{"@type":"ListItem","position":2,"name":"FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome"}]}]}</script>\n<!-- / Yoast SEO plugin. -->',
#   'yoast_head_json': {
#     'title': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd',
#     'robots': {
#       'index': 'index',
#       'follow': 'follow',
#       'max-snippet': 'max-snippet:-1',
#       'max-image-preview': 'max-image-preview:large',
#       'max-video-preview': 'max-video-preview:-1'
#     },
#     'canonical': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/',
#     'og_locale': 'en_US',
#     'og_type': 'article',
#     'og_title': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd',
#     'og_description': '[vc_row][vc_column][vc_text_separator title=&#8221;KEY FEATURES&#8221; i_icon_fontawesome=&#8221;fa fa-book&#8221; i_color=&#8221;sky&#8221; title_align=&#8221;separator_align_left&#8221; add_icon=&#8221;true&#8221;][vc_column_text text_larger=&#8221;no&#8221;] Stunning modern vintage style Swivel function Chrome finish Brass construction Quality',
#     'og_url': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/',
#     'og_site_name': 'Bathroom Sales Direct Pty Ltd',
#     'article_publisher': 'https://www.facebook.com/bathroomsalesdirect/',
#     'article_modified_time': '2021-05-30T11:23:06+00:00',
#     'og_image': [
#       {
#         'width': 1000,
#         'height': 1000,
#         'url': 'https://i2.wp.com/bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg?fit=1000%2C1000&ssl=1', 'path': '/home/bathroo3/public_html/wp-content/uploads/2019/08/202103CC_1.jpg',
#         'size': 'full',
#         'id': 18459,
#         'alt': '',
#         'pixels': 1000000,
#         'type': 'image/jpeg'
#       }
#     ],
#     'twitter_card': 'summary_large_image',
#     'twitter_misc': {
#       'Est. reading time': '1 minute'
#     },
#     'schema': {
#       '@context': 'https://schema.org',
#       '@graph': [
#         {
#           '@type': 'WebSite',
#           '@id': 'https://bathroomsalesdirect.com.au/#website',
#           'url': 'https://bathroomsalesdirect.com.au/',
#           'name': 'Bathroom Sales Direct Pty Ltd',
#           'description': 'For all your bathroom supplies',
#           'potentialAction': [
#             {
#               '@type': 'SearchAction',
#               'target': {
#                 '@type': 'EntryPoint',
#                 'urlTemplate': 'https://bathroomsalesdirect.com.au/?s={search_term_string}'
#               },
#               'query-input': 'required name=search_term_string'
#             }
#           ],
#           'inLanguage': 'en-US'
#         },
#         {
#           '@type': 'ImageObject',
#           '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage',
#           'inLanguage': 'en-US',
#           'url': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg',
#           'contentUrl': 'https://bathroomsalesdirect.com.au/wp-content/uploads/2019/08/202103CC_1.jpg',
#           'width': 1000,
#           'height': 1000
#         },
#         {
#           '@type': 'WebPage',
#           '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#webpage',
#           'url': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/',
#           'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome | Bathroom Sales Direct Pty Ltd',
#           'isPartOf': {
#             '@id': 'https://bathroomsalesdirect.com.au/#website'
#           },
#           'primaryImageOfPage': {
#             '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#primaryimage'
#           },
#           'datePublished': '2019-08-08T12:32:41+00:00',
#           'dateModified': '2021-05-30T11:23:06+00:00',
#           'breadcrumb': {
#             '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb'
#           },
#           'inLanguage': 'en-US',
#           'potentialAction': [
#             {
#               '@type': 'ReadAction',
#               'target': [
#                 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/'
#               ]
#             }
#           ]
#         },
#         {
#           '@type': 'BreadcrumbList',
#           '@id': 'https://bathroomsalesdirect.com.au/product/fienza-eleanor-gooseneck-basin-mixer-chrome-chrome-copy/#breadcrumb',
#           'itemListElement': [
#             {
#               '@type': 'ListItem',
#               'position': 1,
#               'name': 'Shop',
#               'item': 'https://bathroomsalesdirect.com.au/shop_bathroom_supplies/'
#             },
#             {
#               '@type': 'ListItem',
#               'position': 2,
#               'name': 'FIENZA ELEANOR Shepherds Crook Basin Mixer, Chrome / Chrome'
#             }
#           ]
#         }
#       ]
#     }
#   },
#   '_links': {
#     'self': [
#       {
#         'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/products/18457'
#       }
#     ],
#     'collection': [
#       {
#         'href': 'https://bathroomsalesdirect.com.au/wp-json/wc/v3/products'
#       }
#     ]
#   }
# }
