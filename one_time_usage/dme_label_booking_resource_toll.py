# Python 3.6.6

import pysftp
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
import sys, time
import os, base64
import errno
import datetime
import uuid
import redis
import urllib, requests
import pymysql, pymysql.cursors
import json

import time
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, landscape, A6, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, NextPageTemplate, Frame, PageTemplate
from reportlab.platypus.flowables import Spacer, HRFlowable, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code39, code128, code93, qrencoder
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.lib import units
from reportlab.lib import colors
from reportlab.graphics.barcode import createBarcodeDrawing

#registerFont(TTFont('OswaldBold', 'OSWALD-BOLD.TTF'))
#registerFont(TTFont('OswaldRegular', 'OSWALD-REGULAR.TTF'))
#registerFont(TTFont('OswaldItalic', 'OSWALD-BOLD.TTF'))
#registerFont(TTFont('OswaldBoldItalic', 'OSWALD-REGULAR.TTF'))

# registerFontFamily(
#     'Oswald',
#     normal='Oswald-Regular',
#     bold='Oswald-Bold',
#     italic='Oswald-Italic',
#     boldItalic='Oswald-BoldItalic'
#     )

#from reportlab.lib.fonts import addMapping
#addMapping('Oswald', 0, 0, 'OSWALD-REGULAR') #normal
#addMapping('Oswald', 0, 1, 'OSWALD-REGULAR') #italic
#addMapping('Oswald', 1, 0, 'OSWALD-BOLD') #bold
#addMapping('Oswald', 1, 1, 'OSWALD-BOLD') #italic and bold

styles = getSampleStyleSheet()
style_right = ParagraphStyle(name='right', parent=styles['Normal'], alignment=TA_RIGHT)
style_left = ParagraphStyle(name='left', parent=styles['Normal'], alignment=TA_LEFT, leading = 12)
style_center = ParagraphStyle(name='center', parent=styles['Normal'], alignment=TA_CENTER, leading=10)
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

env_mode = 0 # Local
#env_mode = 1 # Dev
# env_mode = 2  # Prod

if env_mode == 0:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = 'root'
    DB_PORT = 3306
    DB_NAME = 'deliver_me'  # Dev
    filepath = "static/toll_au/labels/"
if env_mode == 1:
    DB_HOST = 'deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'oU8pPQxh'
    DB_PORT = 3306
    DB_NAME = 'dme_db_dev'  # Dev
    filepath = "/var/www/html/dme_api/static/dhl_au/labels/"
elif env_mode == 2:
    DB_HOST = 'deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com'
    DB_USER = 'fmadmin'
    DB_PASS = 'oU8pPQxh'
    DB_PORT = 3306
    DB_NAME = 'dme_db_prod'  # Prod
    filepath = "/var/www/html/dme_api/static/dhl_au/labels/"

redis_host = "localhost"
redis_port = 6379
redis_password = ""


def get_is_runnable():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `option_value` FROM `dme_options` WHERE `option_name`=%s"
        cursor.execute(sql, ('rename_move_label'))
        result = cursor.fetchone()
        return int(result['option_value'])

def get_bookings():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT pk_booking_id, b_client_sales_inv_num, b_bookingID_Visual, v_FPBookingNumber, b_clientReference_RA_Numbers, b_client_warehouse_code, b_dateBookedDate, vx_freight_provider, puCompany, pu_Contact_F_L_Name, pu_Phone_Main, pu_Address_Street_1, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, pu_Address_Country, deToCompanyName, puPickUpAvailFrom_Date, pu_PickUp_By_Date, vx_serviceName, de_to_Contact_F_LName, de_to_PickUp_Instructions_Address, de_to_Pick_Up_Instructions_Contact,  de_To_Address_Street_1, de_To_Address_Street_2, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode, de_To_Address_Country, de_to_Contact_FName, de_to_Contact_Lname, de_to_Phone_Main, vx_account_code, s_06_LatestDeliveryDateTimeFinal FROM `dme_bookings` INNER JOIN dme_booking_lines ON dme_bookings.pk_booking_id = dme_booking_lines.fk_booking_id GROUP BY dme_bookings.pk_booking_id ORDER BY dme_bookings.pk_booking_id ASC LIMIT 0,1"
        #  WHERE  b_status='Ready for XML'
        #  WHERE b_client_name = 'Seaway'
        cursor.execute(sql)
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

def get_label_settings( dimension_length, dimension_width ):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT font_family, font_size_small, font_size_medium, font_size_large, label_dimension_length, label_dimension_width, label_image_size_length, label_image_size_width, barcode_dimension_length, barcode_dimension_width FROM label_settings WHERE label_dimension_length = %s AND label_dimension_width = %s"
        adr = ( dimension_length, dimension_width )
        cursor.execute(sql, adr)
        result = cursor.fetchone()
        if result is None:
            sql = "INSERT INTO label_settings (font_family, font_size_small, font_size_medium, font_size_large, label_dimension_length, label_dimension_width, label_image_size_length, label_image_size_width, barcode_dimension_length, barcode_dimension_width) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            adr = ( dimension_length, dimension_width )
            cursor.execute(sql, adr)
            return None
        else:
            return result

def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.rotate(180)
    canvas.restoreState()


def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.rotate(90)
    canvas.restoreState()

def get_barcode_rotated(value, width, barHeight = 27.6 * mm, barWidth = 1, fontSize = 18, humanReadable = True):

    barcode = createBarcodeDrawing('Code128', value = value, barHeight = barHeight, barWidth = barWidth, fontSize = fontSize, humanReadable = humanReadable)

    drawing_width = width
    barcode_scale = drawing_width / barcode.width
    drawing_height = barcode.height * barcode_scale

    drawing = Drawing(drawing_width, drawing_height)
    drawing.scale(barcode_scale, barcode_scale)
    drawing.add(barcode, name='barcode')

    drawing_rotated = Drawing(drawing_height, drawing_width)
    drawing_rotated.rotate(90)
    drawing_rotated.translate(10, -drawing_height)
    drawing_rotated.add(drawing, name='drawing')

    return drawing_rotated

from reportlab.platypus.flowables import Flowable


class verticalText(Flowable):

    '''Rotates a text in a table cell.'''

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        fs = canvas._fontsize
        canvas.translate(1, -fs/1.2)  # canvas._leading?
        canvas.drawString(0, 0, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        fn, fs = canv._fontname, canv._fontsize
        return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)

from reportlab.platypus.flowables import Image

class RotatedImage(Image):

    def wrap(self,availWidth,availHeight):
        h, w = Image.wrap(self,availHeight,availWidth)
        return w, h
    def draw(self):
        self.canv.rotate(90)
        Image.draw(self)

# I = RotatedImage('../images/somelogo.gif')

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



    try:
        #start fetching data from dme_bookings table
        bookings = get_bookings() 
        #end fetching data from dme_bookings table 

        #start check if pdfs folder exists
        if not os.path.exists(filepath):
                os.makedirs(filepath)
        #end check if pdfs folder exists

        #start loop through data fetched from dme_bookings table         
        i = 1
        for booking in bookings:

            #start db query for fetching data from dme_booking_lines table
            booking_lines = get_booking_lines(booking['pk_booking_id'])
            #end db query for fetching data from dme_booking_lines table
            totalQty = 0
            for booking_line in booking_lines:
                totalQty = totalQty + booking_line['e_qty']
            #start pdf file name using naming convention
            #date = datetime.datetime.now().strftime("%Y%m%d")+"_"+datetime.datetime.now().strftime("")
            filename = booking['pu_Address_State'] + "_" + str(booking['v_FPBookingNumber']) + "_"  + str(booking['b_bookingID_Visual']) + ".pdf"
            file = open(filepath+filename, "w") 
            #file.write("Your text goes here") 
            
            #end pdf file name using naming convention

            date = datetime.datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")

            # label_settings = get_label_settings( 146, 104 )[0]
            # print(label_settings)

            label_settings = {'font_family' : 'Verdana', 'font_size_extra_small' : '5', 'font_size_small' : '7.5', 'font_size_medium' : '9', 'font_size_large': '11', 'font_size_extra_large': '13', 'label_dimension_length': '100', 'label_dimension_width': '150', 'label_image_size_length': '90', 'label_image_size_width': '145', 'barcode_dimension_length': '85', 'barcode_dimension_width': '30', 'barcode_font_size': '18', 'line_height_extra_small':'3', 'line_height_small':'5', 'line_height_medium':'6', 'line_height_large':'8'}



            doc = SimpleDocTemplate(filepath+filename, pagesize = ( float(label_settings['label_dimension_length']) * mm, float(label_settings['label_dimension_width']) * mm ), rightMargin = float(float(label_settings['label_dimension_width']) - float(label_settings['label_image_size_width'])) * mm, leftMargin = float(float(label_settings['label_dimension_width']) - float(label_settings['label_image_size_width'])) * mm, topMargin = float(float(label_settings['label_dimension_length']) - float(label_settings['label_image_size_length'])) * mm, bottomMargin = float(float(label_settings['label_dimension_length']) - float(label_settings['label_image_size_length'])) * mm)

            logo = "DME-LOGO.png"
            document = []
            #document.append(im)
            im = Image(logo, 12 * mm, 4 * mm)

            Story=[]
            j = 1
            for booking_line in booking_lines:

                for k in range(booking_line["e_qty"]):

                    tbl_data1 = [
                        [
                            im, 
                            Paragraph('<font size=%s>%s</font>' % (label_settings['font_size_small'], 'CARRIER'), style_center),
                            Paragraph('<font size=%s>DESP: %s</font>' % (label_settings['font_size_small'], booking["b_dateBookedDate"].strftime("%d/%m/%y") if booking["b_dateBookedDate"] else 'N/A'), style_center),
                            Paragraph('<font size=%s><b>%s</b></font>' % (label_settings['font_size_medium'], 'SYD'), style_center),
                            Paragraph('<font size=%s color=%s><b>%s</b></font>' % (label_settings['font_size_extra_large'], colors.white, 'R'), style_center)
                        ],
                        [
                            
                            Paragraph('<font size=%s color=%s><b>%s</b></font>' % (label_settings['font_size_small'], colors.white, booking["vx_serviceName"] if booking["vx_serviceName"] else ' SERVICE'), styles["BodyText"]),
                            
                        ]
                    ]

                    t1 = Table(tbl_data1, colWidths=( float(label_settings['label_image_size_length']) * (1/4) * mm, float(label_settings['label_image_size_length']) * (1/4) * mm, float(label_settings['label_image_size_length']) * (1/4) * mm, float(label_settings['label_image_size_length']) * (1/8) * mm, float(label_settings['label_image_size_length']) * (1/8) * mm ), style = [
                        #('SPAN',(1,0),(1,1)),
                        ('SPAN',(0,1),(2,1)),
                        ('SPAN',(3, 0), (-2, -1)),
                        ('SPAN',(4, 0), (-1, -1)),
                        ('LEFTPADDING',(0,1),(0,1), 5),
                        #('RIGHTPADDING',(1,1),(0,1), 20),
                        #('RIGHTMARGIN',(0,1),(0,1), 20),
                        #('VALIGN',(1,0),(1,0),'TOP'),
                        ('VALIGN',(1,0),(1,0),'BOTTOM'),
                        ('VALIGN',(3, 0), (3, 0),'MIDDLE'),
                        ('VALIGN',(4, 0), (4, 0),'MIDDLE'),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        ('BOX', (3, 0), (3, 1), 1, colors.black),
                        ('BACKGROUND', (0,1), (0,1), colors.black),
                        ('BACKGROUND', (4, 0), (4, 0), colors.black),
                        ('BACKGROUND', (4, 0), (4, 0), colors.black),
                        #('BACKGROUND', (1,0),(1,0), colors.black),
                        ])

                    Story.append(t1)
                    
                    tbl_data1 = [
                        [
                            Paragraph('<font size=%s><b>CONNOTE #</b> %s</font>' % (label_settings['font_size_small'], booking["v_FPBookingNumber"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>TO:</b> %s</font>' % (label_settings['font_size_small'], booking["de_to_Contact_F_LName"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>%s</font>' % (label_settings['font_size_small'],booking["de_To_Address_Street_1"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>%s</font>' % (label_settings['font_size_small'],booking["de_To_Address_Street_2"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>%s</b></font> ' % (label_settings['font_size_small'], booking["de_To_Address_Suburb"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>%s</b></font> ' % (label_settings['font_size_large'], booking["de_To_Address_State"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>%s</b></font> ' % (label_settings['font_size_small'], booking["de_To_Address_PostalCode"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>%s</b></font> ' % (label_settings['font_size_small'], booking["de_To_Address_Country"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>Phone: %s</font> ' % (label_settings['font_size_extra_small'], booking["de_to_Contact_F_LName"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>Contact: %s</font> ' % (label_settings['font_size_extra_small'], booking["de_to_Phone_Main"]), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>Not Before:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s</b></font> ' % (label_settings['font_size_extra_small'], booking["b_dateBookedDate"].strftime("%d/%m/%y %H:%M") if booking["b_dateBookedDate"] else 'N/A'), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>Not After:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s</b></font> ' % (label_settings['font_size_extra_small'], booking["s_06_LatestDeliveryDateTimeFinal"].strftime("%d/%m/%y %H:%M") if booking["s_06_LatestDeliveryDateTimeFinal"] else 'N/A'), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>Special Inst:</b></font>' % label_settings['font_size_extra_small'], style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>%s %s</b></font>' % (label_settings['font_size_extra_small'], str(booking['de_to_PickUp_Instructions_Address']) if booking['de_to_PickUp_Instructions_Address'] else '', str(booking['de_to_Pick_Up_Instructions_Contact']) if booking['de_to_Pick_Up_Instructions_Contact'] else ''), style_left)
                        ],
                        [
                            Paragraph('<font size=%s color=%s><b>Visual Aid Banner</b></font>' % (label_settings['font_size_small'], colors.white), style_center)
                        ]
                    ]

                    t1 = Table(tbl_data1, colWidths=( float(label_settings['label_image_size_length']) * (1/2) * mm ),  rowHeights=( float(label_settings['line_height_extra_small']) * mm ), style = [
                        ('VALIGN',(0,0),(-1,-1),'TOP'),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        ('ALIGN',(0,14), (0,14),'CENTER'),
                        ('BACKGROUND', (0,14), (0,14), colors.black)
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])

                    barcode = booking["v_FPBookingNumber"]+'DESC'+str(k+1).zfill(10)+booking["de_To_Address_PostalCode"]
                    # barcode128 = code128.Code128( barcode, barHeight = 50 * mm, barWidth = 1.4 )
                    barcode128 = get_barcode_rotated(barcode, (float(label_settings['barcode_dimension_length'])) * mm, float(label_settings['barcode_dimension_width']) * mm, 1, float(label_settings['barcode_font_size']), True)

                    d = Drawing(100,100)
                    d.add(Rect(0,0,0,0,strokeWidth=1,fillColor=None))
                    d.add(QrCodeWidget(value='01234567094987654321'))
                    
                    tbl_data4 = [
                        [d],
                    ]
                    t4 = Table(tbl_data4, colWidths = ( float(label_settings['label_image_size_length'])*(1/2) * mm ), rowHeights=( 
                        float(label_settings['line_height_small'] ) * mm
                        ), style = [
                        ('VALIGN',(0,0),(-1,-1),'TOP'),
                        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])

                    data = [[t1, t4]]
                    # adjust the length of tables
                    t1_w = float(label_settings['label_image_size_length'])*(1/2) * mm
                    t4_w = float(label_settings['label_image_size_length'])*(1/2) * mm
                    shell_table = Table(data, colWidths=[t1_w, t4_w], style = [
                        ('VALIGN',(0,0),(-1,-1),'TOP'),
                        # ('SPAN',(0,0),(0,-1)),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])
                    Story.append(shell_table)

                    tbl_data = [
                        [
                            Paragraph('<font size=%s><b>DG\'s<br/> %s<br/></b></font>' % (label_settings['font_size_medium'], 'Yes' if booking_line['e_dangerousGoods'] else 'No'), style_center),
                            Paragraph('<font size=%s><b>ADP<br/></b></font>' % (label_settings['font_size_large']), style_center),
                            Paragraph('<font size=%s><b>Signature<br/> Required<br/></b></font>' % (label_settings['font_size_small']), style_center),
                            Paragraph('<font size=%s><b></b></font>' % (label_settings['font_size_small']), style_center),
                            Paragraph('<font size=%s><b>Item<br/> %s</b></font>' % (label_settings['font_size_extra_small'], str(j).zfill(2)), style_center),
                            Paragraph('<font size=%s><b>L: %s<br/> W: %s<br/> H: %s </b></font>' % (label_settings['font_size_extra_small'], booking_line['e_dimLength'], booking_line['e_dimWidth'], booking_line['e_dimHeight']), style_center),
                            Paragraph('<font size=%s color=%s><b>%s</b><br/></font>' % (label_settings['font_size_small'], colors.white, booking_line['e_Total_KG_weight']), style_center),
                        ]
                    ]
                    t2 = Table(tbl_data, colWidths=((float(label_settings['label_image_size_length'])*(1/7)) * mm), style = [
                        ('BOX', (0, 0), (0, 0), 1, colors.black),
                        ('BOX', (1, 0), (1, 0), 1, colors.black),
                        ('BOX', (2, 0), (2, 0), 1, colors.black),
                        ('BOX', (3, 0), (3, 0), 1, colors.black),
                        ('BOX', (4, 0), (4, 0), 1, colors.black),
                        ('BOX', (5, 0), (5, 0), 1, colors.black),
                        ('BACKGROUND', (6, 0), (6, 0), colors.black),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTMARGIN',(0,0),(-1,-1), 0),
                        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                        ('ALIGN',(0,0),(0,0),'CENTER'),
                        ('INNERGRID', (5,0), (5,0), 10, colors.black),
                        ])

                    Story.append(t2)

                    tbl_data = [
                    	[
                            code128.Code128( barcode, barHeight = 12 * mm, barWidth = .6, humanReadable = True)
                        ],
                        [
                            code128.Code128( barcode, barHeight = 12 * mm, barWidth = .8, humanReadable = True )
                        ],
                    ]

                    t1 = Table(tbl_data, colWidths=( ( float(label_settings['label_image_size_length']) ) * mm ), style = [
                        ('ALIGN',(0,0),(-1,-1),'CENTER'),
                        ('VALIGN',(0,0),(0,-1),'TOP'),
                        ('TOPPADDING',(0,0),(-1,-1), 10),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
                        ('LEFTPADDING',(0,0),(0,-1), 0),
                        ('RIGHTPADDING',(0,0),(0,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])
                    
                    Story.append(t1)

                    Story.append(Spacer(1, 5))

                    tbl_data = [
                    	[
                            Paragraph('<font size=%s><b>From:</b> %s</font>' % ( label_settings['font_size_extra_small'], (booking["puCompany"]) if (booking["puCompany"]) else '' ), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>%s %s</font>' % (label_settings['font_size_extra_small'], str(booking['pu_Address_Suburb']) if booking['pu_Address_Suburb'] else '', str(booking['pu_Address_State']) if booking['pu_Address_State'] else ''), style_left),
                            
                        ],
                        [
                            Paragraph('<font size=%s>%s <b>%s</b></font>' % (label_settings['font_size_extra_small'], str(booking['pu_Address_PostalCode']) if booking['pu_Address_PostalCode'] else '', str(booking['pu_Address_Country']) if booking['pu_Address_Country'] else ''), style_left),
                            
                        ],
                        [
                            Paragraph('<font size=%s>REF: %s</font>' % (label_settings['font_size_extra_small'], str(booking_line['client_item_reference']) if booking_line['client_item_reference'] else ''), style_left),
                            ''
                        ],
                    ]
                    t1 = Table(tbl_data, colWidths=( ( float(label_settings['label_image_size_length']) * (1/2) ) * mm ), rowHeights=( float(label_settings['line_height_extra_small']) * mm ), style = [
                        ('VALIGN',(0, 0),(0, -1),'TOP'),
                        ('TOPPADDING',(40, 40),(-1,-1), 0),
                        ('BOTTOMPADDING',(40, 40),(-1,-1), 0),
                        ('LEFTPADDING',(40, 40),(0,-1), 0),
                        ('RIGHTPADDING',(40, 40),(0,-1), 0),
                        ('TOPMARGIN',(40, 40),(-1,-1), 0),
                        ('BOTTOMMARGIN',(40, 40),(-1,-1), 0),
                        ('LEFTMARGIN',(40, 40),(0,-1), 0),
                        ('RIGHTMARGIN',(40, 40),(0,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])

                    tbl_data = [
                    	[
                            Paragraph('<font size=%s><b>Payee Ac: %s</b></font>' % ( label_settings['font_size_extra_small'], (booking["vx_account_code"]) if booking["vx_account_code"] else '' ), style_left)
                        ],
                        [
                            Paragraph('<font size=%s><b>Contact: %s</b></font>' % (label_settings['font_size_extra_small'], str(booking['pu_Contact_F_L_Name']) if booking['pu_Contact_F_L_Name'] else ''), style_left),
                        ],
                        [
                            Paragraph('<font size=%s><b>PH: %s</b></font>' % (label_settings['font_size_extra_small'], str(booking['pu_Phone_Main']) if booking['pu_Phone_Main'] else ''), style_left)
                        ],
                    ]

                    t4 = Table(tbl_data, colWidths=( ( float(label_settings['label_image_size_length']) ) * mm ), rowHeights=( float(label_settings['line_height_extra_small']) * mm ), style = [
                        ('VALIGN',(0,0),(0,-1),'TOP'),
                        ('TOPPADDING',(20,20),(-1,-1), 0),
                        ('BOTTOMPADDING',(20,20),(-1,-1), 0),
                        ('LEFTPADDING',(20,20),(0,-1), 0),
                        ('RIGHTPADDING',(20,20),(0,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])

                    data = [[t1, t4]]
                    # adjust the length of tables
                    t1_w = float(label_settings['label_image_size_length'])*(1/2) * mm
                    t4_w = float(label_settings['label_image_size_length'])*(1/2) * mm
                    shell_table = Table(data, colWidths=[t1_w, t4_w], style = [
                        ('VALIGN',(0,0),(-1,-1),'TOP'),
                        # ('SPAN',(0,0),(0,-1)),
                        ('TOPPADDING',(0,0),(-1,-1), 0),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                        ('LEFTPADDING',(0,0),(-1,-1), 0),
                        ('RIGHTPADDING',(0,0),(-1,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])
                    Story.append(shell_table)

                    tbl_data = [
                    	[
                            Paragraph('<font size=%s><b>Description of Goods:</b> %s</font>' % ( label_settings['font_size_extra_small'], (booking["puCompany"][:15] + '...') if len(booking["puCompany"]) > 15 else booking["puCompany"] ), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>DECLARATION BY: %s</font>' % (label_settings['font_size_extra_small'], str(booking['pu_Address_PostalCode']) if booking['pu_Address_PostalCode'] else ''), style_left)
                        ],
                        [
                            Paragraph('<font size=%s>%s</font>' % (label_settings['font_size_extra_small'], str(booking['pu_Address_PostalCode']) if booking['pu_Address_PostalCode'] else ''), style_left)
                        ],
                    ]

                    t1 = Table(tbl_data, colWidths=( ( float(label_settings['label_image_size_length']) ) * mm ), rowHeights=( float(label_settings['line_height_extra_small']) * mm ), style = [
                        ('VALIGN',(0,0),(0,-1),'TOP'),
                        ('TOPPADDING',(20,20),(-1,-1), 0),
                        ('BOTTOMPADDING',(20,20),(-1,-1), 0),
                        ('LEFTPADDING',(20,20),(0,-1), 0),
                        ('RIGHTPADDING',(20,20),(0,-1), 0),
                        # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ])
                    
                    Story.append(t1)

                    Story.append(PageBreak())
                
                    j+= 1

            i+= 1
            
            # doc.build(Story)
            doc.build(Story, onFirstPage = myFirstPage, onLaterPages=myLaterPages)
            
            #end formatting pdf file and putting data from db tables

            #with open(filepath+filename, "wb") as fh:
                #tree.write(fh, encoding='UTF-8', xml_declaration=True)
                
                #start copying pdf files to sftp server
                #srv = pysftp.Connection(host="localhost", username="tapas", password="tapas@123", cnopts=cnopts)
                #srv = pysftp.Connection(host="edi.alliedexpress.com.au", username="delvme.external", password="987899e64", cnopts=cnopts)
                #path = 'www'
                #path = 'indata'
                #with srv.cd(path):
                    #srv.put(filepath+filename) 
                
                # Closes the connection
                #srv.close()
                #end copying pdf files to sftp server
            
            #start update booking status in dme_booking table
            #try:
                #fh = open(path+'/'+filename, 'r')
                # Store configuration file values
                #if(os.stat(path+'/'+filename).st_size > 0 and os.path.isfile(path+'/'+filename)):
                    #sql2 = "UPDATE dme_bookings set b_status = %s, z_label_url = %s WHERE pk_booking_id = %s"
                    #adr2 = ('Booked XML', filename, booking[0], )
                    #mycursor.execute(sql2, adr2)
            #except FileNotFoundError as e:
                #print("Error1: "+str(e))
                # Keep preset values
            
            #end update booking status in dme_booking table

            #exit()   
            #end writting data into pdf file
            file.close() 
        #end loop through data fetched from dme_bookings table
         

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(dir(exc_type), fname, exc_tb.tb_lineno)
        #print("Error: unable to fecth data")
        print("Error1: "+str(e))

    print('#901 - Finished %s' % datetime.datetime.now())
    mysqlcon.close()
                    
