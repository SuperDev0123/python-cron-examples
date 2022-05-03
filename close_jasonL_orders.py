# Python 3.6.6
# V 2.0
import time
import datetime
import pymysql, pymysql.cursors

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, DME_API_URL
from _options_lib import get_option, set_option
import subprocess

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
        option = get_option(mysqlcon, "auto_close_jasonL_orders")
        if int(option["option_value"]) == 0:
            print("#905 - `auto_close_jasonL_orders` option is OFF")
        elif option["is_running"]:
            print("#905 - `auto_close_jasonL_orders` script is already RUNNING")
        else:
            print("#906 - `auto_close_jasonL_orders` option is ON")
            set_option(mysqlcon, "auto_close_jasonL_orders", True)
            subprocess.run(
                "python manage.py jasonL_orders_status",
                shell=True,
                check=True,
                cwd=DME_API_URL,
            )
            set_option(mysqlcon, "auto_close_jasonL_orders", False, time1)
    except OSError as e:
        print("#904 Error:", str(e))
        set_option(mysqlcon, "auto_close_jasonL_orders", False, time1)

    mysqlcon.close()
    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
