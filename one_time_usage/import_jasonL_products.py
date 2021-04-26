import csv
import os, sys, time, json
import datetime
import pymysql, pymysql.cursors
import requests
from datetime import datetime, timedelta

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME


def populate(row, mysqlcon):
    cursor = mysqlcon.cursor()
    sql = "INSERT INTO client_products(fk_id_dme_client_id, parent_model_number, child_model_number, description, qty, e_dimUOM, e_weightUOM, e_dimLength, e_dimWidth, e_dimHeight, e_weightPerEach, \
                        z_createdByAccount, z_modifiedByAccount, z_createdTimestamp, z_modifiedTimestamp) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(
        sql,
        (
            21,
            row[1],
            row[1],
            row[0],
            1,
            "m",
            "kg",
            row[3],
            row[9],
            row[2],
            row[8],
            "gold",
            "gold",
            "2021-05-26",
            "2021-05-26",
        ),
    )
    mysqlcon.commit()


def do_process(mysqlcon):
    index = 0

    with open("/Users/juli/Documents/jason_l/products_2021_04_26.csv", "r") as file:
        reader = csv.reader(file)

        for row in reader:
            index += 1

            if index % 1000 == 0:
                print(f"Processing {index}")

            populate(row, mysqlcon)


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
