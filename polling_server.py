import sys
import os
import datetime
import requests
import json
import traceback
import time
import pymysql, pymysql.cursors

from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    USERNAME,
    PASSWORD,
)
from _options_lib import get_option, set_option
from _email_lib import send_email
DEV_SERVER_URL = "http://3.105.62.128/api"
PROD_SERVER_URL = "http://13.55.64.102/api"

def get_token(SERVER_URL):
    url = SERVER_URL + "/api-token-auth/"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)

    if "token" in data0:
        # print("@101 - Token: ", data0["token"])
        return data0["token"]
    else:
        print("@400 - ", data0["non_field_errors"])
        return "400"

def send_email_to_admins(error_msg):
    text = (
        error_msg
    )

    send_email(
        ["bookings@deliver-me.com.au", "goldj@deliver-me.com.au"],
        ["dev.deliverme@gmail.com"],
        f"Error happened while system check",
        text,
    )

def do_process():
    error_msg = "PROD SERVER Check Failed"
    token = get_token(PROD_SERVER_URL)
    if token == "400":
        send_email_to_admins(error_msg)
    error_msg = "DEV SERVER Check Failed"
    token = get_token(DEV_SERVER_URL)
    if token == "400":
        send_email_to_admins(error_msg)

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
        option = get_option(mysqlcon, "system_check")

        if int(option["option_value"]) == 0:
            print("#905 - `system_check` option is OFF")
        elif option["is_running"]:
            print("#905 - `system_check` script is already RUNNING")
        else:
            print("#906 - `system_check` option is ON")
            time1 = time.time()
            set_option(mysqlcon, "system_check", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "system_check", False, time1)
    except Exception as e:
        print("#904 Error: ", str(e))
        set_option(mysqlcon, "system_check", False, time1)

    mysqlcon.close()
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())