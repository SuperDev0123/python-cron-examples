# Python 3.7
# V 1.0
# Released Date: 2020-07-12

from datetime import datetime


def get_option(mysqlcon, flag_name):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT * \
                FROM `dme_options` \
                WHERE option_name=%s"
        cursor.execute(sql, (flag_name))
        dme_option = cursor.fetchone()

        return dme_option


def set_option(mysqlcon, flag_name, is_running):
    with mysqlcon.cursor() as cursor:
        if is_running:
            sql = "UPDATE `dme_options` \
                    SET is_running=%s, start_time=%s, is_running=%s \
                    WHERE option_name=%s"
            cursor.execute(sql, (flag_name, datetime.now(), is_running))
        else:
            sql = "UPDATE `dme_options` \
                    SET is_running=%s, end_time=%s, is_running=%s \
                    WHERE option_name=%s"
            cursor.execute(sql, (flag_name, datetime.now(), is_running))

        mysqlcon.commit()
