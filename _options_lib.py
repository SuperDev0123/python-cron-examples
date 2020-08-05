# Python 3.7
# V 1.0
# Released Date: 2020-07-12

import time
from datetime import datetime


def get_option(mysqlcon, flag_name):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_options` \
                WHERE option_name=%s"
        cursor.execute(sql, (flag_name))
        dme_option = cursor.fetchone()

        return dme_option


def set_option(mysqlcon, flag_name, is_running, start_time=None):
    with mysqlcon.cursor() as cursor:
        if is_running:
            sql = "UPDATE `dme_options` \
                    SET is_running=%s, start_time=%s \
                    WHERE option_name=%s"
            cursor.execute(sql, (is_running, datetime.now(), flag_name))
        else:
            sql = "UPDATE `dme_options` \
                    SET is_running=%s, end_time=%s \
                    WHERE option_name=%s"
            cursor.execute(sql, (is_running, datetime.now(), flag_name))

            time2 = time.time()
            print("#998 Spent time: ", str(int(round(time2 - start_time))), "s")
            sql = "UPDATE `dme_options` \
                    SET elapsed_seconds=%s \
                    WHERE option_name=%s"
            cursor.execute(sql, (str(int(round(time2 - start_time))), flag_name))

        mysqlcon.commit()
