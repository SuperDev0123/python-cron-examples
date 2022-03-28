from cmath import isnan
import math
import pandas as pd
import datetime
import pymysql, pymysql.cursors

production = True  # Dev

if production:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
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

def compare():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT dest_suburb, dest_state, dest_postcode, gateway, onfwd, sort_bin From fp_routing WHERE freight_provider_id=13"
        cursor.execute(sql)
        fp_routings = cursor.fetchall()
        df_db = pd.DataFrame(fp_routings)

    df_sheet = pd.read_excel("ZoneListCommon_04032022112404.xlsx", header=0,converters={'dest_postcode':str,'sort_bin':str})
    df_compare = df_db.astype(str).compare(df_sheet.astype(str), keep_shape=False, align_axis=1)

    update(df_compare)

    # df_compare.to_excel('fp_routing_compare_result.xlsx')

def update(df_compare):
    table = 'fp_routing'
    for index, row in df_compare.iterrows():
        sql_query = f'update {table} set '
        
        if not math.isnan(float(row["dest_postcode"]["self"])):
            sql_query += f'dest_postcode = {row["dest_postcode"]["other"]} ,'
            
        if row["gateway"]["self"] != 'nan':
            sql_query += f"gateway = '{row['gateway']['other']}' ,"

        if row["onfwd"]["self"] != 'nan':
            sql_query += f" onfwd = '{row['onfwd']['other']}' ,"
        sql_query = sql_query[:-1]
        sql_query += f' where id = {index + 1}'
        
        with mysqlcon.cursor() as cursor:
            cursor.execute(sql_query)
        
    mysqlcon.commit()
            

        


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())

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

    compare()

    print("#901 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()