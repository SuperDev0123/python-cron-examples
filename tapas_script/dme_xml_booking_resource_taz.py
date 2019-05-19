# Python 3.6.6

import xml.etree.ElementTree as xml
#from io import BytesIO
import pysftp
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
import sys, time
import os
import errno
import datetime
import uuid
import redis
import urllib, requests
import pymysql, pymysql.cursors

env_mode = 0 # Local
#env_mode = 1 # Dev
# env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = 'fm-prod-database.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
    filepath = "static/xmls/taz_au/"
if env_mode == 1:
    DB_HOST = 'fm-prod-database.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
    filepath = "/var/www/html/dme_api/static/xmls/taz_au/"
elif env_mode == 2:
    DB_HOST = 'fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'Fmadmin1'
    DB_PORT = 3306
    DB_NAME = 'dme_db_prod'  # Prod
    filepath = "/var/www/html/dme_api/static/xmls/taz_au/"

redis_host = "localhost"
redis_port = 6379
redis_password = ""

ACCOUNT_CODE = "SEAWAP"

def get_is_runnable():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `option_value` FROM `dme_options` WHERE `option_name`=%s"
        cursor.execute(sql, ('rename_move_label'))
        result = cursor.fetchone()
        return int(result['option_value'])

def get_bookings():
    with mysqlcon.cursor() as cursor:
        #sql = "SELECT *  FROM `dme_bookings` WHERE b_client_name = 'Seaway'"
        #sql = "SELECT *  FROM `dme_bookings` WHERE b_client_name = %s AND b_status='Ready for XML' GROUP BY dme_bookings.pk_booking_id"
        sql = "SELECT pk_booking_id, b_bookingID_Visual, pu_Address_Street_1, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, pu_Address_Country, deToCompanyName, puPickUpAvailFrom_Date, pu_PickUp_By_Date, vx_serviceName, de_to_PickUp_Instructions_Address, de_to_Pick_Up_Instructions_Contact,  de_To_Address_Street_1, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode, de_To_Address_Country, de_to_Contact_FName, de_to_Contact_Lname, de_to_Phone_Main FROM `dme_bookings` WHERE b_client_name = %s AND pk_booking_id != %s GROUP BY dme_bookings.pk_booking_id"
        adr = ("Seaway", '', )
        #adr = ("Seaway", '8107384115', )
        cursor.execute(sql, adr)
        result = cursor.fetchall()
        if result is None:
            print('@102 - booking empty')
            return None
        else:
            #print('@103 - result: ', result)
            return result

def get_booking_lines(booking_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT e_qty, e_item_type, e_item, e_dimWidth, e_dimLength, e_dimHeight, e_Total_KG_weight, client_item_reference, e_dangerousGoods, e_1_Total_dimCubicMeter FROM dme_booking_lines WHERE fk_booking_id = %s"
        adr = (booking_id, )
        cursor.execute(sql, adr)
        result = cursor.fetchall()
        if result is None:
            print('@102 - booking empty')
            return None
        else:
            #print('@103 - result: ', result)
            return result

if __name__ == '__main__':
    print('#900 - Running %s' % datetime.datetime.now())

    try:
        mysqlcon = pymysql.connect(host=DB_HOST,
                                   port=DB_PORT,
                                   user=DB_USER,
                                   password=DB_PASS,
                                   db=DB_NAME,
                                   charset='utf8mb4',
                                   cursorclass=pymysql.cursors.DictCursor)
    except:
        print('Mysql DB connection error!')
        #exit(1)

    can_run = get_is_runnable()

    if can_run > 0:

        #start method to alter line item type
        def item_type(i):
            if "UHP" in i:
                return 'PCR'
            if "PCR" in i:
                return 'PCR'
            if "LTR" in i:
                return 'LTR'
            if "TBR" in i:
                return 'TBR'
            return i

        try:
            #start fetching data from dme_bookings table
            bookings = get_bookings() 
            #print(bookings)
            #end fetching data from dme_bookings table 

            #start check if xmls folder exists
            if not os.path.exists(filepath):
                    os.makedirs(filepath)
            #end check if xmls folder exists

            #start loop through data fetched from dme_bookings table         
            i = 1
            for booking in bookings:

                #start db query for fetching data from dme_booking_lines table
                booking_lines = get_booking_lines(booking['pk_booking_id'])
                #end db query for fetching data from dme_booking_lines table

                #start calculate total item quantity and total item weight
                totalQty = 0
                totalWght = 0
                for booking_line in booking_lines:
                    totalQty = totalQty + booking_line['e_qty']
                    totalWght = totalWght + booking_line['e_Total_KG_weight']
                #start calculate total item quantity and total item weight

                #start xml file name using naming convention
                date = datetime.datetime.now().strftime("%Y%m%d")+"_"+datetime.datetime.now().strftime("%H%M%S")
                filename = "TAZ_FP_"+date+"_"+str(i)+".xml"
                
                #end xml file name using naming convention

                #start formatting xml file and putting data from db tables
                root = xml.Element("fd:Manifest", **{'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xmlns:fd': "http://www.ezysend.com/FreightDescription/2.0", 'Version': "2.0", 'Action': "Submit", 'Number': "M"+ ACCOUNT_CODE + str(i).zfill(4), 'Type': "Outbound", 'xsi:schemaLocation': "http://www.ezysend.com/FreightDescription/2.0 http://www.ezysend.com/EDI/FreightDescription/2.0/schema.xsd"})

                IndependentContainers = xml.Element("fd:IndependentContainers")
                root.append(IndependentContainers)
                xml.SubElement(IndependentContainers, "fd:Container", **{'Identifier': "IC"+ ACCOUNT_CODE +"00001", 'Volume': "1.02", 'Weight': "200", 'Commodity': "Pallet"})                
                cannote_number = ACCOUNT_CODE +str(i).zfill(5)

                #consignment = xml.Element("fd:Consignment", **{'Number': "DME"+str(booking['b_bookingID_Visual'])})
                consignment = xml.Element("fd:Consignment", **{'Number': cannote_number })
                root.append(consignment)

                Carrier = xml.SubElement(consignment, "fd:Carrier")
                Carrier.text = booking['vx_serviceName']
                AccountCode = xml.SubElement(consignment, "fd:AccountCode")
                AccountCode.text = ACCOUNT_CODE

                senderName = xml.SubElement(consignment, "fd:Sender", **{'Name': ACCOUNT_CODE})
                senderAddress = xml.SubElement(senderName, "fd:Address")
                senderAddressLine1 = xml.SubElement(senderAddress, "fd:Address1")
                senderAddressLine1.text = booking['pu_Address_Street_1']
                senderLocality = xml.SubElement(senderAddress, "fd:Locality")
                senderLocality.text = booking['pu_Address_Suburb']
                senderState = xml.SubElement(senderAddress, "fd:Territory")
                senderState.text = booking['pu_Address_State']
                senderPostcode = xml.SubElement(senderAddress, "fd:PostCode")
                senderPostcode.text = booking['pu_Address_PostalCode']
                senderCountry = xml.SubElement(senderAddress, "fd:Country")
                senderCountry.text = booking['pu_Address_Country']

                companyName = booking['deToCompanyName'].replace("<", "")
                companyName = companyName.replace(">", "")
                companyName = companyName.replace("\"", "")
                companyName = companyName.replace("'", "")
                companyName = companyName.replace("&", "and")

                ReceiverName = xml.SubElement(consignment, "fd:Receiver", **{'Name': companyName, 'Reference': 'CUST0001'})
                ReceiverAddress = xml.SubElement(ReceiverName, "fd:Address")
                ReceiverAddressLine1 = xml.SubElement(ReceiverAddress, "fd:Address1")
                ReceiverAddressLine1.text = booking['de_To_Address_Street_1']
                ReceiverLocality = xml.SubElement(ReceiverAddress, "fd:Locality")
                ReceiverLocality.text = booking['de_To_Address_Suburb']
                ReceiverState = xml.SubElement(ReceiverAddress, "fd:Territory")
                ReceiverState.text = booking['de_To_Address_State']
                ReceiverPostcode = xml.SubElement(ReceiverAddress, "fd:PostCode")
                ReceiverPostcode.text = booking['de_To_Address_PostalCode']
                ReceiverCountry = xml.SubElement(ReceiverAddress, "fd:Country")
                ReceiverCountry.text = booking['de_To_Address_Country']

                ContactName = xml.SubElement(ReceiverName, "fd:ContactName")
                ContactName.text = (str(booking['de_to_Contact_FName']) if booking['de_to_Contact_FName'] else '') + (' ' + str(booking['de_to_Contact_Lname']) if booking['de_to_Contact_Lname'] else '')
                PhoneNumber = xml.SubElement(ReceiverName, "fd:PhoneNumber")
                PhoneNumber.text = (str(booking['de_to_Phone_Main']) if booking['de_to_Phone_Main'] else '')

                FreightForwarderName = xml.SubElement(consignment, "fd:FreightForwarder", **{'Name': companyName})
                FreightForwarderAddress = xml.SubElement(FreightForwarderName, "fd:Address")
                FreightForwarderAddressLine1 = xml.SubElement(FreightForwarderAddress, "fd:Address1")
                FreightForwarderAddressLine1.text = booking['de_To_Address_Street_1']
                FreightForwarderLocality = xml.SubElement(FreightForwarderAddress, "fd:Locality")
                FreightForwarderLocality.text = booking['de_To_Address_Suburb']
                FreightForwarderState = xml.SubElement(FreightForwarderAddress, "fd:Territory")
                FreightForwarderState.text = booking['de_To_Address_State']
                FreightForwarderPostcode = xml.SubElement(FreightForwarderAddress, "fd:PostCode")
                FreightForwarderPostcode.text = booking['de_To_Address_PostalCode']
                FreightForwarderCountry = xml.SubElement(FreightForwarderAddress, "fd:Country")
                FreightForwarderCountry.text = booking['de_To_Address_Country']

                Fragile = xml.SubElement(consignment, "fd:Fragile")
                Fragile.text = 'true'

                ServiceType = xml.SubElement(consignment, "fd:ServiceType")
                ServiceType.text = booking['vx_serviceName']

                DeliveryWindow = xml.SubElement(consignment, "fd:DeliveryWindow", **{'From': booking['puPickUpAvailFrom_Date'].strftime("%Y-%m-%dT%H:%M:%S") if booking['puPickUpAvailFrom_Date'] else '0000-00-00T00:00:00', 'To': booking['pu_PickUp_By_Date'].strftime("%Y-%m-%dT%H:%M:%S") if booking['pu_PickUp_By_Date'] else '0000-00-00T00:00:00'})

                DeliveryInstructions = xml.SubElement(consignment, "fd:DeliveryInstructions")
                DeliveryInstructions.text = str(booking['de_to_PickUp_Instructions_Address']) + ' ' + str(booking['de_to_Pick_Up_Instructions_Contact'])

                #BulkPricing = xml.SubElement(consignment, "fd:BulkPricing")
                #xml.SubElement(BulkPricing, "fd:Container", **{ 'Weight': "500", 'Identifier': "C"+ ACCOUNT_CODE +"00003", 'Volume': "0.001", 'Commodity': "PALLET" }) 
                
                for booking_line in booking_lines:
                    FreightDetails = xml.SubElement(consignment, "fd:FreightDetails", **{ 'Reference': str(booking_line['client_item_reference']) if booking_line['client_item_reference'] else '', 'Quantity': str(booking_line['e_qty']), 'Commodity': (item_type(booking_line['e_item_type']) if booking_line['e_item_type'] else ''), 'CustomDescription': str(booking_line['e_item']) if booking_line['e_item'] else '' })
                    if booking_line['e_dangerousGoods']:
                        DangerousGoods = xml.SubElement(FreightDetails, "fd:DangerousGoods",  **{ 'Class': "1", 'UNNumber': "1003" })
                    
                    ItemDimensions = xml.SubElement(FreightDetails, "fd:ItemDimensions",  **{ 'Length': str(booking_line['e_dimLength']), 'Width': str(booking_line['e_dimWidth']), 'Height': str(booking_line['e_dimHeight']) })

                    ItemWeight = xml.SubElement(FreightDetails, "fd:ItemWeight")
                    ItemWeight.text = (str(booking_line['e_Total_KG_weight']/booking_line['e_qty']) if booking_line['e_qty'] > 0 else 0)

                    ItemVolume = xml.SubElement(FreightDetails, "fd:ItemVolume")
                    ItemVolume.text = (str(booking_line['e_1_Total_dimCubicMeter']))

                    Items = xml.SubElement(FreightDetails, "fd:Items")
                    for j in range(1, booking_line['e_qty']+1):
                        Item = xml.SubElement(Items, "fd:Item", **{ ' Container': "IC" + ACCOUNT_CODE + str(j).zfill(5) })
                        Item.text = "S" + cannote_number + str(j).zfill(3)

                i+= 1
                #end formatting xml file and putting data from db tables

                #start writting data into xml files
                tree = xml.ElementTree(root)
                
                with open(filepath+filename, "wb") as fh:
                    tree.write(fh, encoding='UTF-8', xml_declaration=True)
                    
                    #start copying xml files to sftp server
                    #srv = pysftp.Connection(host="localhost", username="tapas", password="tapas@123", cnopts=cnopts)
                    #srv = pysftp.Connection(host="edi.alliedexpress.com.au", username="delvme.external", password="987899e64", cnopts=cnopts)
                    #path = 'www'
                    #path = 'indata'
                    #with srv.cd(path):
                        #srv.put(filepath+filename) 
                    
                    # Closes the connection
                    #srv.close()
                    #end copying xml files to sftp server
                
                #start update booking status in dme_booking table
                #try:
                    #fh = open(path+'/'+filename, 'r')
                    # Store configuration file values
                    #if(os.stat(path+'/'+filename).st_size > 0 and os.path.isfile(path+'/'+filename)):
                        #sql2 = "UPDATE dme_bookings set b_status = %s, z_xml_url = %s WHERE pk_booking_id = %s"
                        #adr2 = ('Booked XML', filename, booking[0], )
                        #mycursor.execute(sql2, adr2)
                #except FileNotFoundError as e:
                    #print("Error1: "+str(e))
                    # Keep preset values
                
                #end update booking status in dme_booking table

                #exit()   
                #end writting data into xml files
            #end loop through data fetched from dme_bookings table 

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(dir(exc_type), fname, exc_tb.tb_lineno)
            #print("Error: unable to fecth data")
            print("Error1: "+str(e))
    else:
        print('#109 - Flag is 0')

    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()

        




