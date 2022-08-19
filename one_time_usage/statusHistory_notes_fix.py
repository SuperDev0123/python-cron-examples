# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = "dme_db_dev"  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"


def get_statusHistories(mysqlcon):
    """
    find statusHistories which note has duplicated status
    """
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, fk_booking_id, status_old, status_last, notes \
                FROM dme_status_history ORDER BY id ASC"
        cursor.execute(sql)
        results = cursor.fetchall()

        return results


def delete_status_histories(status_histories, mysqlcon):
    """
    delete status_histories
    """
    with mysqlcon.cursor() as cursor:
        for status_history in status_histories:
            sql = "DELETE FROM dme_status_history \
                    WHERE id = %s"
            cursor.execute(sql, (status_history["id"]))
        mysqlcon.commit()


def update_status_histories(status_history, old_status, new_notes, mysqlcon):
    """
    update status_histories
    """
    with mysqlcon.cursor() as cursor:
        sql = "UPDATE dme_status_history \
                SET status_old=%s, notes=%s \
                WHERE id = %s"
        cursor.execute(sql, (old_status, new_notes, status_history["id"]))


def do_process(mysqlcon):
    status_histories = get_statusHistories(mysqlcon)
    print("@0 - ", len(status_histories))

    """
    find note is 'None--->None' and delete all
    """
    # none_status_histories = []
    # for status_history in status_histories:
    #     if (
    #         status_history["notes"] == "None--->None"
    #         or status_history["notes"] == "None ---> None"
    #     ):
    #         print(
    #             "@1 - ",
    #             status_history["notes"],
    #             status_history["status_old"],
    #             status_history["status_last"],
    #         )
    #         none_status_histories.append(status_history)
    # print("@2 - ", len(none_status_histories))
    # delete_status_histories(none_status_histories, mysqlcon)

    """
    find first statusHistories which note is 'Booked--->Booked' and update them
    """
    # booked_status_histories = []
    # for index, status_history in enumerate(status_histories):
    #     if index % 500 == 0:
    #         print("@30 - ", index)

    #     if (
    #         status_history["status_last"] == "Booked"
    #         and status_history["status_old"] == "Booked"
    #         and (
    #             status_history["notes"] == "Booked--->Booked"
    #             or status_history["notes"] == "Booked ---> Booked"
    #         )
    #     ):
    #         new_booked_history = None
    #         for sub_index in reversed(range(index)):
    #             if (
    #                 status_history["fk_booking_id"]
    #                 == status_histories[sub_index]["fk_booking_id"]
    #             ):
    #                 new_booked_history = status_history
    #                 break

    #         if not new_booked_history:
    #             # print(
    #             #     "@31 - ",
    #             #     status_history["notes"],
    #             #     status_history["status_old"],
    #             #     status_history["status_last"],
    #             # )
    #             booked_status_histories.append(status_history)
    # print("@32 - ", len(booked_status_histories))

    # ids = []
    # for status_history in booked_status_histories:
    #     ids.append(str(status_history["id"]))
    # print("@33 - ", ", ".join(ids))

    ### Should update via mysql GUI

    """
    find statusHistories which notes have same statues
    """
    wrong_status_histories = []
    for index, status_history in enumerate(status_histories):
        if index % 500 == 0:
            print("@30 - ", index, status_history["id"])

        if (
            status_history["notes"]
            and " ---> " in status_history["notes"]
            and status_history["notes"].split(" ---> ")[0]
            == status_history["notes"].split(" ---> ")[1]
        ):
            prev_history = None

            for sub_index in reversed(range(index)):
                if (
                    status_history["fk_booking_id"]
                    == status_histories[sub_index]["fk_booking_id"]
                ):
                    prev_history = status_histories[sub_index]
                    print("@1 - ", status_history["id"], prev_history["id"])
                    break

            if (
                prev_history
                and prev_history["status_last"] != status_history["status_last"]
            ):
                print(
                    "@3 - ",
                    status_history["id"],
                    status_history["fk_booking_id"],
                    status_history["status_old"],
                    status_history["notes"],
                    status_history["status_last"],
                )
                print(
                    "44 - ",
                    status_history["id"],
                    status_history["fk_booking_id"],
                    prev_history["status_last"],
                    f"{prev_history['status_last']} ---> {status_history['status_last']}",
                    status_history["status_last"],
                )
                update_status_histories(
                    status_history,
                    prev_history["status_last"],
                    f"{prev_history['status_last']} ---> {status_history['status_last']}",
                    mysqlcon,
                )
                wrong_status_histories.append(status_history)

            # if not prev_history:
            #     if (
            #         status_history["notes"] == "Booked--->Booked"
            #         or status_history["notes"] == "Booked ---> Booked"
            #     ):
            #         print(
            #             "@3 - ",
            #             status_history["id"],
            #             status_history["fk_booking_id"],
            #             status_history["status_old"],
            #             status_history["notes"],
            #             status_history["status_last"],
            #         )
            #         print(
            #             "4 - ",
            #             status_history["id"],
            #             status_history["fk_booking_id"],
            #             "Ready for Booking",
            #             f"Ready for Booking--->{status_history['status_last']}",
            #             status_history["status_last"],
            #         )
            #         wrong_status_histories.append(status_history)

    print("@4 - ", len(wrong_status_histories))

    mysqlcon.commit()


if __name__ == "__main__":
    print("#900 - Started %s" % datetime.datetime.now())

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
        do_process(mysqlcon)
    except OSError as e:
        print("Error 904:", str(e))

    print("#909 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
