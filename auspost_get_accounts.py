# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option


def do_update_service_code():
    url = API_URL + "/fp-api/auspost/update-service-code/"
    data = {}

    response = requests.post(url, params={}, json=data)
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)
    return s0


def do_process(mysqlcon):
    time.sleep(5)
    result = do_update_service_code()


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

    try:
        option = get_option(mysqlcon, "auspost_get_accounts")

        if int(option["option_value"]) == 0:
            print("#905 - `auspost_get_accounts` option is OFF")
        elif option["is_running"]:
            print("#905 - `auspost_get_accounts` script is already RUNNING")
        else:
            print("#906 - `auspost_get_accounts` option is ON")
            set_option(mysqlcon, "auspost_get_accounts", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "auspost_get_accounts", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "auspost_get_accounts", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s" % datetime.datetime.now())
