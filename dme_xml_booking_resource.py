# api/xml_booking_resource.py
from tastypie.resources import ModelResource
from api.models import Note
import xml.etree.ElementTree as xml
import datetime
import os
#from io import BytesIO
import pysftp
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

class XmlBookingResource(ModelResource):
    class Meta:

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

        #start method to alter line item type

        #start db connection
        import mysql.connector
        mydb = mysql.connector.connect(
          host="fm-dev-database.cbx3p5w50u7o.us-west-2.rds.amazonaws.com",
          user="fmadmin",
          passwd="Fmadmin1",
          database="dme_db_dev"
        )
        mycursor = mydb.cursor()
        #end db connection

        #start db query for fetching data from dme_bookings table
        sql = "SELECT pk_booking_id, pu_Address_Street_1, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, v_FPBookingNumber, puPickUpAvailFrom_Date, vx_serviceName, total_1_KG_weight_override, deToCompanyName, de_To_Address_Street_1, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode  FROM dme_bookings WHERE b_client_name = %s AND b_status='Ready for XML' GROUP BY dme_bookings.pk_booking_id"
        #sql = "SELECT dme_bookings.pk_booking_id,  FROM dme_bookings LEFT JOIN dme_booking_lines ON dme_bookings.pk_booking_id = dme_booking_lines.fk_booking_id WHERE b_client_name = %s GROUP BY dme_bookings.pk_booking_id"
        adr = ("Seaway", )
        #end db query for fetching data from dme_bookings table
        try:
            #start fetching data from dme_bookings table
            mycursor.execute(sql, adr)
            bookings = mycursor.fetchall()  
            #end fetching data from dme_bookings table 

            #start check if xmls folder exists
            filepath = "static/xmls/"
            #filepath = "/var/www/html/dme_api/static/xmls/"
            if not os.path.exists(filepath):
                    os.makedirs(filepath)
            #end check if xmls folder exists

            #start loop through data fetched from dme_bookings table         
            i = 1
            for booking in bookings:

                #start db query for fetching data from dme_booking_lines table
                sql1 = "SELECT e_qty, e_item_type, e_item, e_dimWidth, e_dimLength, e_dimHeight, e_Total_KG_weight FROM dme_booking_lines WHERE fk_booking_id = %s"
                adr1 = (booking[0], )
                mycursor.execute(sql1, adr1)
                booking_lines = mycursor.fetchall() 

                #print(booking[1]);exit();
                #end db query for fetching data from dme_booking_lines table

                #start calculate total item quantity and total item weight
                totalQty = 0
                totalWght = 0
                for booking_line in booking_lines:
                    totalQty = totalQty + booking_line[0]
                    totalWght = totalWght + booking_line[6]
                #start calculate total item quantity and total item weight

                #start xml file name using naming convention
                date = datetime.datetime.now().strftime("%Y%m%d")+"_"+datetime.datetime.now().strftime("%H%M%S")
                filename = "AL_HANALT_"+date+"_"+str(i)+".xml"
                i+= 1
                #end xml file name using naming convention

                #start formatting xml file and putting data from db tables
                root = xml.Element("AlTransportData", **{'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
                consignmentHeader = xml.Element("ConsignmentHeader")
                root.append(consignmentHeader)
                chargeAccount = xml.SubElement(consignmentHeader, "ChargeAccount")
                chargeAccount.text = "HANALT"
                senderName = xml.SubElement(consignmentHeader, "SenderName")
                senderName.text = "Hankook"
                senderAddressLine1 = xml.SubElement(consignmentHeader, "SenderAddressLine1")
                senderAddressLine1.text = booking[1]
                senderLocality = xml.SubElement(consignmentHeader, "SenderLocality")
                senderLocality.text = booking[2]
                senderState = xml.SubElement(consignmentHeader, "SenderState")
                senderState.text = booking[3]
                senderPostcode = xml.SubElement(consignmentHeader, "SenderPostcode")
                senderPostcode.text = booking[4]

                companyName = booking[9].replace("<", "")
                companyName = companyName.replace(">", "")
                companyName = companyName.replace("\"", "")
                companyName = companyName.replace("'", "")
                companyName = companyName.replace("&", "and")
                
                consignmentShipments = xml.Element("ConsignmentShipments")
                root.append(consignmentShipments)
                consignmentShipment = xml.SubElement(consignmentShipments, "ConsignmentShipment")
                ConsignmentNumber = xml.SubElement(consignmentShipment, "ConsignmentNumber")
                ConsignmentNumber.text = booking[0]
                DespatchDate = xml.SubElement(consignmentShipment, "DespatchDate")
                DespatchDate.text = str(booking[6])
                CarrierService = xml.SubElement(consignmentShipment, "CarrierService")
                CarrierService.text = booking[7]
                totalQuantity = xml.SubElement(consignmentShipment, "totalQuantity")
                totalQuantity.text = str(totalQty)
                totalWeight = xml.SubElement(consignmentShipment, "totalWeight")
                totalWeight.text = str(totalWght)
                ReceiverName = xml.SubElement(consignmentShipment, "ReceiverName")
                ReceiverName.text = companyName
                ReceiverAddressLine1 = xml.SubElement(consignmentShipment, "ReceiverAddressLine1")
                ReceiverAddressLine1.text = booking[10]
                ReceiverLocality = xml.SubElement(consignmentShipment, "ReceiverLocality")
                ReceiverLocality.text = booking[11]
                ReceiverState = xml.SubElement(consignmentShipment, "ReceiverState")
                ReceiverState.text = booking[12]
                ReceiverPostcode = xml.SubElement(consignmentShipment, "ReceiverPostcode")
                ReceiverPostcode.text = booking[13]

                ItemsShipment = xml.SubElement(consignmentShipment, "ItemsShipment")
                
                for booking_line in booking_lines:
                    #print('UHP' in booking_line[1])
                    Item = xml.SubElement(ItemsShipment, "Item")
                    Quantity = xml.SubElement(Item, "Quantity")
                    Quantity.text = str(booking_line[0])
                    ItemType = xml.SubElement(Item, "ItemType")
                    ItemType.text = item_type(booking_line[1])
                    ItemDescription = xml.SubElement(Item, "ItemDescription")
                    ItemDescription.text = booking_line[2]
                    Width = xml.SubElement(Item, "Width")
                    Width.text = str(booking_line[3])
                    Length = xml.SubElement(Item, "Length")
                    Length.text = str(booking_line[4])
                    Height = xml.SubElement(Item, "Height")
                    Height.text = str(booking_line[5])
                    DeadWeight = xml.SubElement(Item, "DeadWeight")
                    DeadWeight.text = str(booking_line[6]/booking_line[0])

                    SSCCs = xml.SubElement(Item, "SSCCs")
                    SSCC = xml.SubElement(SSCCs, "SSCC")
                    SSCC.text = booking[0]
                #end formatting xml file and putting data from db tables

                #start writting data into xml files
                tree = xml.ElementTree(root)
                with open(filepath+filename, "wb") as fh:
                    tree.write(fh, encoding='UTF-8', xml_declaration=True)

                    #start copying xml files to sftp server
                    srv = pysftp.Connection(host="localhost", username="tapas", password="tapas@123", cnopts=cnopts)
                    #srv = pysftp.Connection(host="edi.alliedexpress.com.au", username="delvme.external", password="987899e64", cnopts=cnopts)
                    path = 'www'
                    #path = 'indata'
                    with srv.cd(path):
                        srv.put(filepath+filename) 

                    # Closes the connection
                    srv.close()
                    #end copying xml files to sftp server
                
                #start update booking status in dme_booking table
                try:
                    fh = open(path+'/'+filename, 'r')
                    # Store configuration file values
                    if(os.stat(path+'/'+filename).st_size > 0 and os.path.isfile(path+'/'+filename)):
                        sql2 = "UPDATE dme_bookings set b_status = %s, z_xml_url = %s WHERE pk_booking_id = %s"
                        adr2 = ('Booked XML', filename, booking[0], )
                        mycursor.execute(sql2, adr2)
                except FileNotFoundError as e:
                    print("Error: "+str(e))
                    # Keep preset values
                
                #end update booking status in dme_booking table

                #exit()   
                #end writting data into xml files
            #end loop through data fetched from dme_bookings table 

        except Exception as e:
            #print("Error: unable to fecth data")
            print("Error: "+str(e))
        mydb.close()
        queryset = Note.objects.all()
        object_class = None
        resource_name = 'processxml'

        




