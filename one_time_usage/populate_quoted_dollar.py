import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME, API_URL


def get_bookings(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, inv_cost_quoted, inv_sell_quoted, b_status, vx_freight_provider, pk_booking_id \
                FROM `dme_bookings` \
                WHERE `b_client_name`=%s and `b_dateBookedDate` is not NULL and `x_manual_booked_flag`=%s and \
                b_status not in ('Cancelled', 'Closed', 'Ready for Booking', 'Entered') and inv_cost_quoted is not NULL \
                ORDER BY id DESC \
                LIMIT 2000"
        cursor.execute(sql, ("Tempo Pty Ltd", 0))
        bookings = cursor.fetchall()

        return bookings


def update_booking(booking, cost_fl, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "UPDATE dme_bookings SET inv_cost_quoted=%s WHERE id=%s"
    cursor.execute(sql, (cost_fl, booking["id"]))
    mysqlcon.commit()


def get_quotes(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT id, fee, fk_freight_provider_id \
                FROM `api_booking_quotes` \
                WHERE `fk_client_id` = %s"
        cursor.execute(sql, ("Tempo Pty Ltd"))
        quotes = cursor.fetchall()

        return quotes


def update_quote(quote, quoted_dollar, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "UPDATE api_booking_quotes SET client_mu_1_minimum_values=%s WHERE id=%s"
    cursor.execute(sql, (quoted_dollar, quote["id"]))
    mysqlcon.commit()


def do_process(mysqlcon):
    # bookings = get_bookings(mysqlcon)
    # print("Bookings cnt:", len(bookings))

    capital_fl = 0.1341
    hunter_fl = 0.18
    tnt_fl = 0.192
    sendle_fl = 0

    client_markup_percent = 0.15
    client_min_markup_startingcostvalue = 20
    client_min_markup_value = 18

    # fk_booking_ids = []
    # for booking in bookings:
    #     fk_booking_ids.append('"' + booking["pk_booking_id"] + '"')

    quotes = get_quotes(mysqlcon)
    print("Quotes cnt:", len(quotes))

    for quote in quotes:
        quoted_dollar = 0
        fp_markupfuel_levy_percent = 0

        if quote["fk_freight_provider_id"].lower() == "capital":
            fp_markupfuel_levy_percent = capital_fl
        elif quote["fk_freight_provider_id"].lower() == "tnt":
            fp_markupfuel_levy_percent = tnt_fl
        elif quote["fk_freight_provider_id"].lower() == "hunter":
            fp_markupfuel_levy_percent = hunter_fl

        cost_fl = float(quote["fee"]) * (1 + fp_markupfuel_levy_percent)

        if cost_fl < float(client_min_markup_startingcostvalue):
            quoted_dollar = cost_fl * (1 + client_markup_percent)
        else:
            cost_mu = cost_fl * client_markup_percent

            if cost_mu > client_min_markup_value:
                quoted_dollar = cost_fl + cost_mu
            else:
                quoted_dollar = cost_fl + client_min_markup_value

        update_quote(quote, quoted_dollar, mysqlcon)


if __name__ == "__main__":
    print("#900 Started %s" % datetime.datetime.now())

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
    print("#999 Finished %s\n\n\n" % datetime.datetime.now())
