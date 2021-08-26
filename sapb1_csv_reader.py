# Python 3.7

import sys
import os
import time
import json
import datetime
import pymysql
import traceback
import requests
import shutil

from _env import (
    API_URL,
    USERNAME,
    PASSWORD,
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    API_URL,
    SAPB1_CSV_INPUT_DIR,
    SAPB1_CSV_INPUT_ACHIEVE_DIR,
)
from _options_lib import get_option, set_option
from _email_lib import send_email


def _login():
    url = f"{API_URL}/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response0 = requests.post(url, json=data)
    response0 = response0.content.decode("utf8")
    data0 = json.loads(response0)
    token = data0["token"]
    print("@201 - Logged in")
    return token


def _get_bok_1s(b_client_sales_inv_nums, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = (
        "SELECT pk_auto_id, b_client_order_num, b_client_sales_inv_num, success "
        + f"FROM bok_1_headers WHERE b_client_sales_inv_num in ({b_client_sales_inv_nums})"
    )
    cursor.execute(sql)
    bok_1s = cursor.fetchall()
    return bok_1s


def do_process(fpath, mysqlcon):
    print(f"#911 - Processing: {fpath}")
    csv_lines = []
    b_client_sales_inv_nums = []

    print(f"#912 - Reading CSV file")
    with open(fpath) as csv_file:
        for i, line in enumerate(csv_file):
            if len(line.split("|")) != 3:
                error_msg = f"#913 - File has wrong line - {i}: {line}"
                send_email(
                    [],
                    ["dev.deliverme@gmail.com"],
                    "Error on 'SAPB1 CSV READER'",
                    error_msg,
                )
                raise Exception(error_msg)

            csv_lines.append(line)
            b_client_sales_inv_nums.append(line.split("|")[1])

    print(f"#914 - Finish reading CSV file")
    token = _login()
    bok_1s = _get_bok_1s(", ".join(b_client_sales_inv_nums), mysqlcon)
    # print("#900 - Read bok_1s", bok_1s)

    for bok_1 in bok_1s:
        for line in csv_lines:
            b_client_order_num = line.split("|")[0]
            b_client_sales_inv_num = line.split("|")[1]
            # print(f"@915 - b_client_order_num: {b_client_order_num}, b_client_sales_inv_num: {b_client_sales_inv_num}")

            if b_client_sales_inv_num == bok_1["b_client_sales_inv_num"]:
                b_client_sales_inv_nums.remove(b_client_sales_inv_num)

                if not bok_1["b_client_order_num"]:
                    cursor = mysqlcon.cursor()
                    sql = "UPDATE bok_1_headers SET b_client_order_num=%s WHERE b_client_sales_inv_num=%s"
                    cursor.execute(sql, (b_client_order_num, b_client_sales_inv_num))
                    mysqlcon.commit()

                if bok_1["success"] == "3":
                    url = f"{API_URL}/external/paperless/send_order_to_paperless/"
                    headers = {"Authorization": f"JWT {token}"}
                    data = {"b_client_sales_inv_num": b_client_sales_inv_num}
                    response = requests.post(url, headers=headers, json=data)

                    if response.status_code != 200:
                        print(
                            f"@921 - Failed to send order to Paperless: {b_client_sales_inv_num}"
                        )
                    else:
                        print(
                            f"@922 - Success to send order to Paperless: {b_client_sales_inv_num}"
                        )

    print(
        "@929 - Not matching b_client_sales_inv_nums:",
        ", ".join(b_client_sales_inv_nums),
    )


if __name__ == "__main__":
    print("#900 Started %s" % datetime.datetime.now())
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
    except Exception as e:
        print("Mysql DB connection error!", e)
        exit(1)

    if not os.path.exists(SAPB1_CSV_INPUT_DIR):
        print("#901 SAPB1 CSV(input) dir does not exist! path:", SAPB1_CSV_INPUT_DIR)
        exit(1)

    try:
        option = get_option(mysqlcon, "sapb1_csv_reader")

        if int(option["option_value"]) == 0:
            print("#905 - `sapb1_csv_reader` option is OFF")
        elif option["is_running"]:
            print("#905 - `sapb1_csv_reader` script is already RUNNING")
        else:
            print("#906 - `sapb1_csv_reader` option is ON")
            set_option(mysqlcon, "sapb1_csv_reader", True)
            print("#910 - Get started processing...")

            for fname in os.listdir(SAPB1_CSV_INPUT_DIR):
                fpath = os.path.join(SAPB1_CSV_INPUT_DIR, fname)

                if os.path.isfile(fpath) and fname.endswith(".csv"):
                    do_process(fpath, mysqlcon)

                shutil.move(
                    SAPB1_CSV_INPUT_DIR + fname, SAPB1_CSV_INPUT_ACHIEVE_DIR + fname
                )
                print(f"@930 - Moved .CSV file to 'archive'")

            set_option(mysqlcon, "sapb1_csv_reader", False, time1)
    except Exception as e:
        traceback.print_exc()
        print("Error 904:", str(e))
        set_option(mysqlcon, "sapb1_csv_reader", False, time1)

    mysqlcon.close()
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())
