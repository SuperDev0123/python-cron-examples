# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import json
import uuid
import requests

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

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
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    API_URL = "http://3.105.62.128/api"  # Dev
    # API_URL = "http://13.55.64.102/api"  # Prod
else:
    API_URL = "http://localhost:8000/api"  # Local

if IS_PRODUCTION:
    OK_DIR = "/dme_sftp/plum_au/ok/indata/"
    ARCHIVE_OK_DIR = "/dme_sftp/plum_au/ok/archive/"
else:
    OK_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
    ARCHIVE_OK_DIR = "/Users/admin/work/goldmine/scripts/dir02/"


def _is_eof(f):
    cur = f.tell()
    f.seek(0, os.SEEK_END)
    end = f.tell()
    f.seek(cur, os.SEEK_SET)
    return cur == end


def _login():
    url = f"{API_URL}/api-token-auth/"
    data = {"username": "dme", "password": "pass#123"}
    response0 = requests.post(url, json=data)
    response0 = response0.content.decode("utf8")
    data0 = json.loads(response0)
    token = data0["token"]
    print("@201 - Logged in")
    return token


def _read_file(ok_file):
    bok_1 = {}
    bok_2 = []

    bok_1["hdr"] = ok_file.read(3).strip()
    bok_1["picks"] = ok_file.read(10).strip()
    bok_1["document_number"] = ok_file.read(20).strip()
    bok_1["number_product_lines"] = ok_file.read(4).strip()
    bok_1["business_parter_code"] = ok_file.read(6).strip()
    bok_1["bp_name"] = ok_file.read(50).strip()
    bok_1["delivery_address1"] = ok_file.read(50).strip()
    bok_1["delivery_address2"] = ok_file.read(50).strip()
    bok_1["city"] = ok_file.read(50).strip()
    bok_1["postcode"] = ok_file.read(10).strip()
    bok_1["customer_order_number"] = ok_file.read(8).strip()
    bok_1["priority"] = ok_file.read(2).strip()
    bok_1["order_type"] = ok_file.read(2).strip()
    bok_1["tel_no_instructions"] = ok_file.read(225).strip()
    bok_1["pick_instructions"] = ok_file.read(29).strip()
    bok_1["state"] = ok_file.read(3).strip()
    bok_1["service"] = ok_file.read(21).strip()
    bok_1["email_address"] = ok_file.read(50).strip()
    bok_1["phone_number"] = ok_file.read(20).strip()

    while not _is_eof(ok_file):
        bok_2_line = {}
        bok_2_line["dtl"] = ok_file.read(3).strip()
        bok_2_line["picks"] = ok_file.read(10).strip()
        bok_2_line["document_number"] = ok_file.read(20).strip()
        bok_2_line["line_number"] = ok_file.read(4).strip()
        bok_2_line["customer_product_code"] = ok_file.read(15).strip()
        bok_2_line["quantity"] = ok_file.read(12).strip()
        bok_2_line["height"] = ok_file.read(20).strip()
        bok_2_line["width"] = ok_file.read(20).strip()
        bok_2_line["length"] = ok_file.read(20).strip()
        bok_2_line["weight"] = ok_file.read(20).strip()

        if not bok_2_line["dtl"] == "":
            bok_2.append(bok_2_line)

    return bok_1, bok_2


def _populate_file(bok_1, bok_2):
    header = {}
    lines = []

    header["pk_header_id"] = str(uuid.uuid1())
    header["client_booking_id"] = bok_1["document_number"]
    header["b_000_b_total_lines"] = int(bok_1["number_product_lines"])
    header["b_054_b_del_company"] = bok_1["bp_name"]
    header["b_061_b_del_contact_full_name"] = bok_1["bp_name"]
    header["b_055_b_del_address_street_1"] = bok_1["delivery_address1"]
    header["b_056_b_del_address_street_2"] = bok_1["delivery_address2"]
    header["b_059_b_del_address_postalcode"] = bok_1["postcode"]
    header["b_057_b_del_address_state"] = bok_1["state"]
    header["b_client_order_num"] = bok_1["customer_order_number"]
    header["b_client_del_note_num"] = bok_1["customer_order_number"]
    header["b_009_b_priority"] = bok_1["priority"]
    header["b_043_b_del_instructions_contact"] = bok_1["tel_no_instructions"]
    header["b_015_b_pu_instructions_contact"] = bok_1["pick_instructions"]
    header["b_003_b_service_name"] = bok_1["service"]
    header["success"] = 2  # Hardcoded start
    header["fk_client_id"] = "461162D2-90C7-BF4E-A905-000000000003"
    header["b_client_name"] = "Plum"
    header["b_client_warehouse_code"] = "No - Warehouse"
    header["fk_client_warehouse_id"] = 100
    header["b_027_b_pu_address_type"] = "Business"
    header["b_028_b_pu_company"] = "Plum Products AUS"
    header["b_029_b_pu_address_street_1"] = "Suite 303/156 Military Rd"
    header["b_030_b_pu_address_street_2"] = ""
    header["b_031_b_pu_address_state"] = "NSW"
    header["b_032_b_pu_address_suburb"] = "Neutral Bay"
    header["b_033_b_pu_address_postalcode"] = "2089"
    header["b_034_b_pu_address_country"] = "Australia"
    header["b_035_b_pu_contact_full_name"] = "plum contacttest"
    header["b_037_b_pu_email"] = bok_1["email_address"]
    header["b_038_b_pu_phone_main"] = bok_1["phone_number"]
    header["b_021_b_pu_avail_from_date"] = str(datetime.datetime.now())  # Hardcoded end

    for bok_2_line in bok_2:
        line = {}
        line["fk_header_id"] = header["pk_header_id"]
        line["client_booking_id"] = bok_1["document_number"]
        line["v_client_pk_consigment_num"] = bok_2_line["document_number"]
        line["l_003_item"] = bok_2_line["customer_product_code"]
        line["l_002_qty"] = int(float(bok_2_line["quantity"]))
        line["success"] = 2  # Hardcoded start
        line["l_004_dim_UOM"] = "mm"
        line["l_005_dim_length"] = bok_2_line["length"]
        line["l_006_dim_width"] = bok_2_line["width"]
        line["l_007_dim_height"] = bok_2_line["height"]
        line["l_008_weight_UOM"] = "kg"
        line["l_009_weight_per_each"] = bok_2_line["weight"]  # Hardcoded end
        lines.append(line)

    return header, lines


def _push_2_tables(header, lines, mysqlcon, fname):
    token = _login()

    url = f"{API_URL}/bok_1_headers/"
    headers = {"Authorization": f"JWT {token}"}
    response = requests.post(url, headers=headers, json=header)

    if response.status_code != 201:
        print(f"@203 - Failed Pushed bok_1_headers: {header['pk_header_id']}")
    else:
        print(f"@202 - Pushed bok_1_headers: {header['pk_header_id']}")

        for line in lines:
            url = f"{API_URL}/bok_2_lines/"
            headers = {"Authorization": f"JWT {token}"}
            response = requests.post(url, headers=headers, json=line)

        shutil.move(OK_DIR + fname, ARCHIVE_OK_DIR + fname)
        print(f"@205 - Moved .ok file to 'archive'")


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
        for fname in sorted(os.listdir(OK_DIR)):
            fpath = os.path.join(OK_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".ok"):
                print("#901 Detect .ok file:", fpath)
                ok_file = open(fpath, "r")
                bok_1, bok_2 = _read_file(ok_file)
                # print(bok_1, "\n", bok_2)
                header, lines = _populate_file(bok_1, bok_2)
                # print(header, "\n", lines)
                _push_2_tables(header, lines, mysqlcon, fname)

    except OSError as e:
        print(str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
