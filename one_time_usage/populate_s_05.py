import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests
from datetime import datetime, timedelta

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = """
                SELECT id, s_05_Latest_Pick_Up_Date_TimeSet, b_dateBookedDate, puPickUpAvailFrom_Date, pu_PickUp_Avail_Time_Hours, pu_PickUp_Avail_Time_Minutes
                FROM dme_bookings
                WHERE s_05_Latest_Pick_Up_Date_TimeSet IS NOT NULL OR b_dateBookedDate IS NOT NULL;
            """
        cursor.execute(sql)
        bookings = cursor.fetchall()

        return bookings


def update_booking(booking, mysqlcon):
    cursor = mysqlcon.cursor()
    # sql = "UPDATE dme_bookings SET puPickUpAvailFrom_Date=%s, pu_PickUp_Avail_Time_Hours=%s, pu_PickUp_Avail_Time_Minutes=%s, s_05_Latest_Pick_Up_Date_TimeSet=%s WHERE id=%s"
    # cursor.execute(
    #     sql,
    #     (
    #         booking["puPickUpAvailFrom_Date"],
    #         booking["pu_PickUp_Avail_Time_Hours"],
    #         booking["pu_PickUp_Avail_Time_Minutes"],
    #         booking["s_05_Latest_Pick_Up_Date_TimeSet"],
    #         booking["id"],
    #     ),
    # )
    sql = "UPDATE dme_bookings SET puPickUpAvailFrom_Date=%s, s_05_Latest_Pick_Up_Date_TimeSet=%s WHERE id=%s"
    cursor.execute(
        sql,
        (
            booking["puPickUpAvailFrom_Date"],
            booking["s_05_Latest_Pick_Up_Date_TimeSet"],
            booking["id"],
        ),
    )
    mysqlcon.commit()


def do_process(mysqlcon):
    bookings = get_bookings(mysqlcon)
    print("Bookings cnt:", len(bookings))

    for booking in bookings:
        ### Phase #1

        # if (
        #     booking["puPickUpAvailFrom_Date"]
        #     and booking["pu_PickUp_Avail_Time_Hours"] is None
        # ):
        #     booking["pu_PickUp_Avail_Time_Hours"] = 10

        # if (
        #     not booking["puPickUpAvailFrom_Date"]
        #     or not booking["s_05_Latest_Pick_Up_Date_TimeSet"]
        # ):
        #     print(
        #         f'#100 Booking PK:{booking["id"]}, Booked Date: {booking["b_dateBookedDate"]}'
        #     )

        #     is_booked_after_cutoff = False
        #     booked_hour = booking["b_dateBookedDate"].time().hour + 10

        #     if booked_hour > 24:
        #         booked_hour = booked_hour - 24

        #     if booked_hour > 12:
        #         is_booked_after_cutoff = True

        #     if is_booked_after_cutoff:
        #         booking["puPickUpAvailFrom_Date"] = (
        #             booking["b_dateBookedDate"] + timedelta(days=1)
        #         ).date()
        #         booking["pu_PickUp_Avail_Time_Hours"] = 10
        #         booking["pu_PickUp_Avail_Time_Minutes"] = 0
        #         booking["s_05_Latest_Pick_Up_Date_TimeSet"] = booking[
        #             "b_dateBookedDate"
        #         ] + timedelta(days=1)
        #         booking["s_05_Latest_Pick_Up_Date_TimeSet"].replace(hour=0)
        #     else:
        #         booking["puPickUpAvailFrom_Date"] = booking["b_dateBookedDate"].date()
        #         booking["pu_PickUp_Avail_Time_Hours"] = (
        #             (booking["b_dateBookedDate"] + timedelta(hours=10)).time().hour
        #         )
        #         booking["pu_PickUp_Avail_Time_Minutes"] = (
        #             booking["b_dateBookedDate"].time().minute
        #         )
        #         booking["s_05_Latest_Pick_Up_Date_TimeSet"] = booking[
        #             "b_dateBookedDate"
        #         ]

        #     print(
        #         f'#200 Booked Next Day: {is_booked_after_cutoff}, PU From: {booking["puPickUpAvailFrom_Date"]}, {booking["pu_PickUp_Avail_Time_Hours"]}:{booking["pu_PickUp_Avail_Time_Minutes"]}'
        #     )

        ### Phase #2

        print(
            f'#100 Booking PK:{booking["id"]}, Booked Date: {booking["b_dateBookedDate"]}, s_05: {booking["s_05_Latest_Pick_Up_Date_TimeSet"]}'
        )

        if booking["puPickUpAvailFrom_Date"]:
            weekno = booking["puPickUpAvailFrom_Date"].weekday()

            if weekno > 4:
                booking["puPickUpAvailFrom_Date"] = booking[
                    "puPickUpAvailFrom_Date"
                ] + timedelta(days=7 - weekno)
                print(f'@200 - Booked Date: {booking["puPickUpAvailFrom_Date"]}')

        if booking["s_05_Latest_Pick_Up_Date_TimeSet"]:
            weekno = booking["s_05_Latest_Pick_Up_Date_TimeSet"].weekday()

            if weekno > 4:
                booking["s_05_Latest_Pick_Up_Date_TimeSet"] = booking[
                    "s_05_Latest_Pick_Up_Date_TimeSet"
                ] + timedelta(days=7 - weekno)
                print(f'@300 - s_05: {booking["s_05_Latest_Pick_Up_Date_TimeSet"]}')

        update_booking(booking, mysqlcon)


if __name__ == "__main__":
    print("#900 Started %s" % datetime.now())

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
        print("#910 - Processing...")
        do_process(mysqlcon)
    except Exception as e:
        print("#904 Error: ", str(e))

    mysqlcon.close()
    print("#999 Finished %s" % datetime.now())
