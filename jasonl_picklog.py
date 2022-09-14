"""
Python version 3.7.0
Script version 1.0

Avaialble clients:
    * Jason L
"""

import traceback
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests
import subprocess

from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    API_URL,
    USERNAME,
    PASSWORD,
)
from _options_lib import get_option, set_option
from _email_lib import send_email
from email_reader import update_booking, _check_quote


LOG_ID = "[JASONL PICKLOG]"


def get_token():
    url = API_URL + "/api-token-auth/"
    data = {"username": "jason.l_bizsystem", "password": "(Pkm7s,9]Z&Fyw9Q"}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return None


def do_process(mysqlcon, token):
    print(f"@351 {LOG_ID} Running .sh script...")
    subprocess.run(["/home/ubuntu/jason_l/picklog/src/run.sh"])
    print(f"@352 {LOG_ID} Finish running .sh")
    file_path = "/home/ubuntu/jason_l/picklog/src/picklog.csv"
    csv_file = open(file_path)
    print(f"@350 {LOG_ID} File({file_path}) opened!")

    for i, line in enumerate(csv_file):
        if i == 0:  # Ignore first header row
            continue

        content_items = line.split("|")
        order_number = content_items[0].strip()
        shipping_type = content_items[1].strip()
        address_type = content_items[2].strip()

        # Prevent '135000-' case
        if len(order_number.split("-")) > 1 and order_number.split("-")[1] == "":
            order_number = order_number.split("-")[0]

        print(f"@801 - {line}")
        is_updated = update_booking(
            mysqlcon, order_number, shipping_type, address_type, token
        )

        print(
            f"\n@802 - order_number: {order_number}, {'MAPPED!' if is_updated else 'NOT MAPPED'}"
        )

        if is_updated:
            _check_quote(order_number, mysqlcon)


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

    try:
        option = get_option(mysqlcon, "jasonl_picklog")

        if int(option["option_value"]) == 0:
            print("#905 - `jasonl_picklog` option is OFF")
        elif option["is_running"]:
            print("#905 - `jasonl_picklog` script is already RUNNING")
        else:
            token = get_token()
            print("#906 - `jasonl_picklog` option is ON")
            time1 = time.time()
            set_option(mysqlcon, "jasonl_picklog", True)
            print("#910 - Processing...")
            do_process(mysqlcon, token)
            print("#919 - Finished processing!")
            set_option(mysqlcon, "jasonl_picklog", False, time1)
    except Exception as e:
        traceback.print_exc()
        print("#904 Error: ", str(e))
        set_option(mysqlcon, "jasonl_picklog", False, time1)

    mysqlcon.close()
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())
