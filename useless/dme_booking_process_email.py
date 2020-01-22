#! /usr/bin/python

import smtplib
import sys, time
import os, base64
import datetime
import email
import email.mime.application
import pymysql, pymysql.cursors

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from os.path import basename

from email.mime.text import MIMEText
from subprocess import Popen, PIPE

# env_mode = 0  # Local
# env_mode = 1 # Dev
env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
    filepath = "static/common/labels/"
if env_mode == 1:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_dev"  # Dev
    filepath = "/var/www/html/dme_api/static/dhl_au/labels/"
elif env_mode == 2:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    DB_NAME = "dme_db_prod"  # Prod
    filepath = "/var/www/html/dme_api/static/dhl_au/labels/"

# start function to get booking data by v_FPBookingNumber
def get_bookings():
    with mysqlcon.cursor() as cursor:
        sql = """\
            SELECT pk_booking_id, b_bookingID_Visual, v_FPBookingNumber, b_clientReference_RA_Numbers, vx_fp_order_id, fp_invoice_no, vx_futile_Booking_Notes, b_client_warehouse_code, b_dateBookedDate, s_21_Actual_Delivery_TimeStamp, vx_freight_provider, vx_freight_provider_carrier, vx_Transit_Duration, pu_Address_Street_1, de_To_Address_City, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, pu_Address_Country, vx_fp_pu_eta_time, deToCompanyName, puPickUpAvailFrom_Date, pu_PickUp_By_Date, vx_serviceName, de_to_Contact_F_LName, de_to_PickUp_Instructions_Address, pu_Contact_F_L_Name, b_handling_Instructions, z_calculated_ETA, vx_fp_del_eta_time, de_to_Pick_Up_Instructions_Contact,  de_To_Address_Street_1, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode, de_To_Address_Country, de_to_Contact_FName, de_to_Contact_Lname, pu_Operting_Hours, de_Operating_Hours, DME_Notes, de_to_Phone_Main, z_label_url
             FROM `dme_bookings` LEFT JOIN dme_booking_lines ON dme_booking_lines.fk_booking_id = dme_bookings.pk_booking_id LIMIT 0,5
            """

        cursor.execute(sql)
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


# end function to get booking data by v_FPBookingNumber

# start function to get booking data by v_FPBookingNumber
def get_booking(b_bookingID_Visual):
    with mysqlcon.cursor() as cursor:
        sql = """\
            SELECT pk_booking_id, b_bookingID_Visual, v_FPBookingNumber, b_clientReference_RA_Numbers, vx_fp_order_id, fp_invoice_no, vx_futile_Booking_Notes, b_client_warehouse_code, b_dateBookedDate, s_21_Actual_Delivery_TimeStamp, vx_freight_provider, vx_freight_provider_carrier, vx_Transit_Duration, pu_Address_Street_1, de_To_Address_City, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, pu_Address_Country, vx_fp_pu_eta_time, deToCompanyName, puPickUpAvailFrom_Date, pu_PickUp_By_Date, vx_serviceName, de_to_Contact_F_LName, de_to_PickUp_Instructions_Address, pu_Contact_F_L_Name, b_handling_Instructions, z_calculated_ETA, vx_fp_del_eta_time, de_to_Pick_Up_Instructions_Contact,  de_To_Address_Street_1, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode, de_To_Address_Country, de_to_Contact_FName, de_to_Contact_Lname, pu_Operting_Hours, de_Operating_Hours, DME_Notes, de_to_Phone_Main, z_label_url
             FROM `dme_bookings` LEFT JOIN dme_booking_lines ON dme_booking_lines.fk_booking_id = dme_bookings.pk_booking_id WHERE b_bookingID_Visual IN (%s) LIMIT 5
            """
        print(sql)
        cursor.execute(sql, b_bookingID_Visual)
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


# end function to get booking data by v_FPBookingNumber

# start function to get booking line data by booking_id
def get_booking_lines(booking_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT e_qty, e_item_type, e_item, e_type_of_packaging, e_dimWidth, e_dimLength, e_dimHeight, e_Total_KG_weight, client_item_reference, e_dangerousGoods, e_1_Total_dimCubicMeter, e_spec_clientRMA_Number, e_spec_customerReferenceNo, e_weightUOM, e_dimUOM FROM dme_booking_lines WHERE fk_booking_id = %s"
        adr = (booking_id,)
        cursor.execute(sql, adr)
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


# end function to get booking line data by booking_id

# start function to get email template by emailName
def get_email_template(emailName):
    with mysqlcon.cursor() as cursor:
        sql = """\
            SELECT whenAttachmentUnavailable, sectionName, id, fk_idEmailParent,  emailName, emailBodyRepeatOdd, emailBodyRepeatEven,emailBody
             FROM `dme_email_templates` WHERE emailName = %s
            """
        cursor.execute(sql, (emailName))
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


# end function to get email template by emailName

# # start function to get send email
# def send_email(send_to, subject, text, files=None, server="localhost", use_tls=True):

#     msg = MIMEMultipart()
#     msg["From"] = "noreply@localhost"
#     msg["To"] = COMMASPACE.join(send_to)
#     msg["Date"] = formatdate(localtime=True)
#     msg["Subject"] = subject

#     msg.attach(MIMEText(text))

#     for f in files or []:
#         with open(f, "rb") as fil:
#             part = MIMEApplication(fil.read(), Name=basename(f))
#         part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
#         msg.attach(part)

#     smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)

#     if use_tls:
#         smtp.starttls()

#     smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
#     smtp.sendmail(settings.EMAIL_HOST_USER, send_to, msg.as_string())
#     smtp.close()


# def send_email1(
#     from_email, to_email, subject, text, files=None, server="localhost", use_tls=True
# ):
#     # Create message container - the correct MIME type is multipart/alternative.
#     msg = MIMEMultipart("alternative")
#     msg["Subject"] = subject
#     msg["From"] = from_email
#     msg["To"] = to_email

#     msg.attach(MIMEText(text))

#     for f in files or []:
#         with open(f, "rb") as fil:
#             part = MIMEApplication(fil.read(), Name=basename(f))
#         part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
#         msg.attach(part)

#     # # Send the message via local SMTP server.
#     mail = smtplib.SMTP("localhost", 1025)
#     mail.set_debuglevel(True)  # show communication with the server

#     # # sendmail function takes 3 arguments: sender's address, recipient's address
#     # # and message to send - here it is sent as one string.
#     try:
#         mail.sendmail(from_email, to_email, msg.as_string())
#     finally:
#         mail.quit()


# end function to get send email

# start function to preprocess email data from db table
def send_booking_email_using_template(emailName, b_bookingID_Visual):
    # templates = get_email_template(emailName)
    templates = []
    header = """
        <figure class="table">
            <table>
                <tbody>
                    <tr>
                        <td colspan="3">Hi {TOADDRESSCONTACT},</td></tr><tr><td colspan="3">&nbsp;</td>
                    </tr>
                    <tr>
                        <td colspan="3">Please book this in for tomorrow and let me know how many vehicles are you going to use. Please ask the driver to have the attached delivery dockets signed by the store as it will serve as the POD. Thank you.</td>
                    </tr>
                    <tr>
                        <td colspan="3"><strong>Will be collected from ACFS. Please ask the driver to go through the breezeway to avoid longer waiting time.&nbsp;</strong></td>
                    </tr>
                    <tr>
                        <td colspan="3">&nbsp;</td></tr><tr><td>Delivery window is between {DELIVERY_OPERATING_HOURS}.</td><td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td colspan="3">&nbsp;</td></tr><tr><td>these are the bookings that are checked on all bookings page.</td><td>&nbsp;</td><td>&nbsp;</td>
                    </tr>
                </tbody>
            </table>
        </figure>
    """

    footer = """
        <figure class="table">
        <TABLE style = 'border-collapse: collapse; font-family: verdana; text-align: justify; text-justify: inter-word;line-height: 7px;'>
            <tr>
                <TD colspan = '3' width = '600px'>&nbsp;</TD>
            </tr>
            <tr>
                <TD colspan = '3' width = '600px'>&nbsp;</TD>
            </tr>
            <tr>
                <td colspan="3">Kind Regards,</td></tr><tr><td colspan="3">&nbsp;</td>
            </tr>
            <tr>
                <td colspan="3"><b>Nen - Bookings @ Deliver ME</b></td></tr><tr><td colspan="3">&nbsp;</td>
            </tr>
            <tr>
                <td colspan="3">DELIVER-ME PTY LTD</td></tr><tr><td colspan="3">&nbsp;</td>
            </tr>
            <tr>
                <td colspan="3"><b>T:</b> +61 2 8311 1500 <b>E:</b> bookings@deliver-me.com.au</td></tr><tr><td colspan="3">&nbsp;</td>
            </tr>
        </TABLE>
        </figure>
    """

    html = """\
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html>

    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>A responsive two column example</title>
        
    </head>

    <body>"""

    html += header

    html += """ 
        <figure class="table">   
        <table border="1" cellpadding="5" style = 'border-collapse: collapse; font-family: verdana;'>
            <thead>
                <TR style='color:#ffffff; '>
                <TD height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Document No.</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Location Code</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Order Number</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>External Document No.</TD>
                <TD height='25px' width = '100px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Sell-to Customer No.</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Sell-to Customer Name</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Ship-to Name</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Ship-to Address</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Ship-to City</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Ship-to Country</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Ship-to Postcode</TD>
                <TD height='25px' width = '200px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #fff1c6; color: #000000; text-align: center'>Pallet Count</TD>
              </TR>
            </thead>
            <tbody>
            </figure>
            """
    bookings = get_bookings()

    for data in bookings:
        # start db query for fetching data from dme_booking_lines table
        booking_lines = get_booking_lines(data["pk_booking_id"])
        # end db query for fetching data from dme_booking_lines table

        totalQty = 0
        totalWeight = 0
        for booking_line in booking_lines:
            totalQty = totalQty + booking_line["e_qty"] if booking_line["e_qty"] else 0
            totalWeight = (
                totalWeight + booking_line["e_Total_KG_weight"]
                if booking_line["e_Total_KG_weight"]
                else 0
            )
        html += """\
            <tr>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
                <td height='25px' width = '900px' style='font-weight: bold; border:1px solid #b3b3b3; background-color: #ffffff; text-align: center'>%s</td>
            </tr>
            """ % (
            data["b_bookingID_Visual"],
            data["de_To_Address_Suburb"],
            data["vx_fp_order_id"],
            data["fp_invoice_no"],
            data["de_to_Phone_Main"],
            data["de_to_Contact_F_LName"],
            data["de_to_Contact_F_LName"],
            data["de_To_Address_Street_1"],
            data["de_To_Address_City"],
            data["de_To_Address_Country"],
            data["de_To_Address_PostalCode"],
            totalQty,
        )

    html += footer
    html += """
        </body>
        </html>
    """

    # print(html)
    fp1 = open("dme_booking_process_email.html", "w+")
    fp1.write(html)

    to_email = "icss666@gmail.com"
    from_email = "noreply@localhost"
    subject = (
        "Tempo "
        + emailName
        + " - DME# "
        + str(data["v_FPBookingNumber"])
        + " / Freight Provider# "
        + str(data["vx_freight_provider"])
    )
    # send_booking_email_using_template
    # send_email1(from_email, to_email, subject, html, files)
    # send_email(to_email, subject, html)


# end function to preprocess email data from db table

# Driver program
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
        # exit(1)

    try:
        template = "Futile Pickup"
        b_bookingID_Visual = "132375, 132464, 132456"
        send_booking_email_using_template(template, b_bookingID_Visual)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(dir(exc_type), fname, exc_tb.tb_lineno)
        # print("Error: unable to fecth data")
        print("Error1: " + str(e))

    print("#901 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
