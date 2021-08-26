# Python 3.6.6
# V 2.0
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL
from _options_lib import get_option, set_option

# Available FPs for `update service code`
AVAILABLE_FPS = ["AUSPOST"]


def do_update_service_code(fp_name):
    url = API_URL + f"/fp-api/{fp_name}/update-service-code/"
    response = requests.post(url, params={}, json={})
    response0 = response.content.decode("utf8")
    data0 = json.loads(response0)
    s0 = json.dumps(data0, indent=4, sort_keys=True)  # Just for visual
    print("@220 - ", s0)
    return s0


def do_process(mysqlcon):
    for fp_name in AVAILABLE_FPS:
        print("@100 - Freight Provider name:", fp_name)
        result = do_update_service_code(fp_name.lower())


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
        option = get_option(mysqlcon, "update_service_code")

        if int(option["option_value"]) == 0:
            print("#905 - `update_service_code` option is OFF")
        elif option["is_running"]:
            print("#905 - `update_service_code` script is already RUNNING")
        else:
            print("#906 - `update_service_code` option is ON")
            set_option(mysqlcon, "update_service_code", True)
            print("#910 - Processing...")
            do_process(mysqlcon)
            set_option(mysqlcon, "update_service_code", False, time1)
            print("#919 - Finished!")
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "update_service_code", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
