# Python 3.7.0

import sys, time
import os, base64
import errno
import datetime
import uuid
import urllib, requests
import pymysql, pymysql.cursors
import json

from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, landscape, A6, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    NextPageTemplate,
    Frame,
    PageTemplate,
    TableStyle,
)
from reportlab.platypus.flowables import Image, Spacer, HRFlowable, PageBreak, Flowable
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

from _env import DB_HOST, DB_USER, DB_PASS, DB_PORT, DB_NAME

styles = getSampleStyleSheet()
style_right = ParagraphStyle(name="right", parent=styles["Normal"], alignment=TA_RIGHT)
style_left = ParagraphStyle(
    name="left", parent=styles["Normal"], alignment=TA_LEFT, leading=12
)
style_center = ParagraphStyle(
    name="center", parent=styles["Normal"], alignment=TA_CENTER, leading=10
)
styles.add(ParagraphStyle(name="Justify", alignment=TA_JUSTIFY))

filepath = "./"


def get_is_runnable():
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `option_value` FROM `dme_options` WHERE `option_name`=%s"
        cursor.execute(sql, ("rename_move_label"))
        result = cursor.fetchone()
        return int(result["option_value"])


def get_booking(pk):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT pk_booking_id, b_bookingID_Visual, v_FPBookingNumber, b_clientReference_RA_Numbers, b_client_warehouse_code, b_dateBookedDate, vx_freight_provider, puCompany, pu_Contact_F_L_Name, pu_Phone_Main, pu_Address_Street_1, pu_Address_Street_2, pu_Address_Suburb, pu_Address_State, pu_Address_PostalCode, pu_Address_Country, deToCompanyName, puPickUpAvailFrom_Date, pu_PickUp_By_Date, vx_serviceName, de_to_Contact_F_LName, de_to_PickUp_Instructions_Address, de_to_Pick_Up_Instructions_Contact,  de_To_Address_Street_1, de_To_Address_Street_2, de_To_Address_Suburb, de_To_Address_State, de_To_Address_PostalCode, de_To_Address_Country, de_to_Contact_FName, de_to_Contact_Lname, de_to_Phone_Main, vx_account_code, s_06_LatestDeliveryDateTimeFinal, vx_fp_pu_eta_time, vx_fp_del_eta_time FROM `dme_bookings` WHERE id=%s"
        cursor.execute(sql, (pk))
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


def get_booking_lines(booking_id):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT e_qty, e_item_type, e_item, e_dimWidth, e_dimLength, e_dimHeight, e_Total_KG_weight, client_item_reference, e_dangerousGoods, e_1_Total_dimCubicMeter, e_weightUOM FROM dme_booking_lines WHERE fk_booking_id = %s"
        adr = (booking_id,)
        cursor.execute(sql, adr)
        result = cursor.fetchall()
        if result is None:
            print("@102 - booking empty")
            return None
        else:
            # print('@103 - result: ', result)
            return result


def get_label_settings(dimension_length, dimension_width):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT font_family, font_size_small, font_size_medium, font_size_large, label_dimension_length, label_dimension_width, label_image_size_length, label_image_size_width, barcode_dimension_length, barcode_dimension_width FROM label_settings WHERE label_dimension_length = %s AND label_dimension_width = %s"
        adr = (dimension_length, dimension_width)
        cursor.execute(sql, adr)
        result = cursor.fetchone()
        if result is None:
            sql = "INSERT INTO label_settings (font_family, font_size_small, font_size_medium, font_size_large, label_dimension_length, label_dimension_width, label_image_size_length, label_image_size_width, barcode_dimension_length, barcode_dimension_width) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            adr = (dimension_length, dimension_width)
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


def get_barcode_rotated(
    value, width, barHeight=27.6 * mm, barWidth=1, fontSize=18, humanReadable=True
):

    barcode = createBarcodeDrawing(
        "Code128",
        value=value,
        barHeight=barHeight,
        barWidth=barWidth,
        fontSize=fontSize,
        humanReadable=humanReadable,
    )

    drawing_width = width
    barcode_scale = drawing_width / barcode.width
    drawing_height = barcode.height * barcode_scale

    drawing = Drawing(drawing_width, drawing_height)
    drawing.scale(barcode_scale, barcode_scale)
    drawing.add(barcode, name="barcode")

    drawing_rotated = Drawing(drawing_height, drawing_width)
    drawing_rotated.rotate(90)
    drawing_rotated.translate(10, -drawing_height)
    drawing_rotated.add(drawing, name="drawing")

    return drawing_rotated


class verticalText(Flowable):

    """Rotates a text in a table cell."""

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        fs = canvas._fontsize
        canvas.translate(1, -fs / 1.2)  # canvas._leading?
        canvas.drawString(0, 0, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        fn, fs = canv._fontname, canv._fontsize
        return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)


class RotatedImage(Image):
    def wrap(self, availWidth, availHeight):
        h, w = Image.wrap(self, availHeight, availWidth)
        return w, h

    def draw(self):
        self.canv.rotate(90)
        Image.draw(self)


# I = RotatedImage('../images/somelogo.gif')

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
        # exit(1)

    try:
        print("GET BOOKINGS")
        # start fetching data from dme_bookings table
        bookings = get_booking(71656)
        # end fetching data from dme_bookings table

        print("BOOKINGS 1111")

        # start check if pdfs folder exists
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        # end check if pdfs folder exists

        # start loop through data fetched from dme_bookings table
        print("bookings", bookings)
        i = 1
        for booking in bookings:

            # start db query for fetching data from dme_booking_lines table
            booking_lines = get_booking_lines(booking["pk_booking_id"])
            # end db query for fetching data from dme_booking_lines table
            totalQty = 0
            for booking_line in booking_lines:
                totalQty = totalQty + booking_line["e_qty"]
            # start pdf file name using naming convention
            # date = datetime.datetime.now().strftime("%Y%m%d")+"_"+datetime.datetime.now().strftime("")
            filename = (
                booking["pu_Address_State"]
                + "_"
                + str(booking["v_FPBookingNumber"])
                + "_"
                + str(booking["b_bookingID_Visual"])
                + ".pdf"
            )
            file = open(filepath + filename, "w")
            # file.write("Your text goes here")

            # end pdf file name using naming convention

            date = datetime.datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")

            # label_settings = get_label_settings( 146, 104 )[0]
            # print(label_settings)

            label_settings = {
                "font_family": "Verdana",
                "font_size_extra_small": "5",
                "font_size_small": "7.5",
                "font_size_medium": "9",
                "font_size_large": "11",
                "font_size_extra_large": "13",
                "label_dimension_length": "100",
                "label_dimension_width": "150",
                "label_image_size_length": "95",
                "label_image_size_width": "145",
                "barcode_dimension_length": "85",
                "barcode_dimension_width": "30",
                "barcode_font_size": "18",
                "line_height_extra_small": "3",
                "line_height_small": "5",
                "line_height_medium": "6",
                "line_height_large": "8",
            }

            doc = SimpleDocTemplate(
                filepath + filename,
                pagesize=(
                    float(label_settings["label_dimension_length"]) * mm,
                    float(label_settings["label_dimension_width"]) * mm,
                ),
                rightMargin=float(
                    float(label_settings["label_dimension_width"])
                    - float(label_settings["label_image_size_width"])
                )
                * mm,
                leftMargin=float(
                    float(label_settings["label_dimension_width"])
                    - float(label_settings["label_image_size_width"])
                )
                * mm,
                topMargin=float(
                    float(label_settings["label_dimension_length"])
                    - float(label_settings["label_image_size_length"])
                )
                * mm,
                bottomMargin=float(
                    float(label_settings["label_dimension_length"])
                    - float(label_settings["label_image_size_length"])
                )
                * mm,
            )

            # logo = "StarTrack-Logo.png"
            document = []
            # document.append(im)
            # im = Image(logo, 12 * mm, 4 * mm)
            # print(im)

            dme_logo = "dme_logo.png"
            dme_im = Image(dme_logo, 30 * mm, 8 * mm)

            Story = []
            j = 1

            print("booking_lines", booking_lines)
            for booking_line in booking_lines:

                for k in range(booking_line["e_qty"]):

                    tbl_data1 = [[dme_im]]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 3)
                            * mm
                        ),
                        rowHeights=(float(label_settings["line_height_large"]) * mm),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (0, -1), "TOP"),
                        ],
                    )

                    tbl_data2 = [
                        [
                            Paragraph(
                                "<font size=%s><b>%s</b></font>"
                                % (
                                    label_settings["font_size_extra_large"],
                                    (booking["vx_freight_provider"])
                                    if (booking["vx_freight_provider"])
                                    else "",
                                ),
                                style_center,
                            )
                        ]
                    ]

                    t2 = Table(
                        tbl_data2,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 3)
                            * mm
                        ),
                        rowHeights=(float(label_settings["line_height_medium"]) * mm),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (0, -1), "TOP"),
                        ],
                    )
                    barcode = str(j).zfill(2)

                    tbl_data3 = [[Paragraph("", style_left)]]

                    t3 = Table(
                        tbl_data3,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (0, -1), "TOP"),
                        ],
                    )

                    data = [[t1, t2, t3]]

                    t1_w = (
                        float(label_settings["label_image_size_length"]) * (1 / 3) * mm
                    )
                    t2_w = (
                        float(label_settings["label_image_size_length"]) * (1 / 3) * mm
                    )
                    t3_w = (
                        float(label_settings["label_image_size_length"]) * (1 / 3) * mm
                    )

                    shell_table = Table(
                        data,
                        colWidths=[t1_w, t2_w, t2_w],
                        style=[
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            # ('SPAN',(0,0),(0,-1)),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMBORDER", (0, 0), (-1, -1), 0),
                            # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ],
                    )

                    hr = HRFlowable(
                        width=(float(label_settings["label_image_size_length"]) * mm),
                        thickness=1,
                        lineCap="square",
                        color=colors.black,
                        spaceBefore=1,
                        spaceAfter=1,
                        hAlign="CENTER",
                        vAlign="BOTTOM",
                        dash=None,
                    )

                    Story.append(shell_table)
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s>Connote:%s </font>"
                                % (
                                    label_settings["font_size_medium"],
                                    (booking["v_FPBookingNumber"])
                                    if (booking["v_FPBookingNumber"])
                                    else "",
                                ),
                                style_left,
                            ),
                            Paragraph(
                                "<font size=%s><b>%s</b></font> "
                                % (label_settings["font_size_extra_large"], "SYD-EST"),
                                style_left,
                            ),
                        ],
                        [
                            Paragraph(
                                "<font size=%s>Order: %s</font>"
                                % (label_settings["font_size_medium"], ""),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>Date:  %s</font> "
                                % (
                                    label_settings["font_size_medium"],
                                    booking["b_dateBookedDate"].strftime("%d/%m/%Y")
                                    if booking["b_dateBookedDate"]
                                    else "N/A",
                                ),
                                style_left,
                            )
                        ],
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 2)
                            * mm,
                            float(label_settings["label_image_size_length"])
                            * (1 / 2)
                            * mm,
                        ),
                        rowHeights=(
                            float(label_settings["line_height_extra_small"]) * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ],
                    )

                    Story.append(t1)
                    Story.append(Spacer(1, 5))
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    barcode = "PRD" + booking["de_To_Address_PostalCode"] + "R1"

                    tbl_data1 = [
                        [
                            code128.Code128(
                                barcode,
                                barHeight=10 * mm,
                                barWidth=1,
                                humanReadable=True,
                            )
                        ]
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (2 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ],
                    )
                    Story.append(t1)
                    Story.append(Spacer(1, 10))
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s><b>TO:</b> %s %s</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    booking["de_to_Contact_F_LName"],
                                    (booking["puCompany"])
                                    if (booking["puCompany"])
                                    else "",
                                ),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>  %s</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    booking["de_To_Address_Street_1"],
                                ),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>  %s</font> "
                                % (label_settings["font_size_medium"], ""),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>  %s</font> "
                                % (
                                    label_settings["font_size_medium"],
                                    booking["de_To_Address_Suburb"],
                                ),
                                style_left,
                            )
                        ],
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (2 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ],
                    )

                    d = Drawing(80, 80)
                    d.add(Rect(0, 0, 0, 0, strokeWidth=1, fillColor=None))
                    d.add(QrCodeWidget(value="01234567"))

                    tbl_data2 = [[d]]
                    t2 = Table(
                        tbl_data2,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ],
                    )

                    data = [[t1, t2]]

                    t1_w = (
                        float(label_settings["label_image_size_length"]) * (2 / 3) * mm
                    )
                    t2_w = (
                        float(label_settings["label_image_size_length"]) * (1 / 3) * mm
                    )

                    shell_table = Table(
                        data,
                        colWidths=[t1_w, t2_w],
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ],
                    )
                    Story.append(shell_table)
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s>Insts: %s %s</font>"
                                % (
                                    label_settings["font_size_small"],
                                    str(booking["de_to_PickUp_Instructions_Address"])
                                    if booking["de_to_PickUp_Instructions_Address"]
                                    else "",
                                    str(booking["de_to_Pick_Up_Instructions_Contact"])
                                    if booking["de_to_Pick_Up_Instructions_Contact"]
                                    else "",
                                ),
                                style_left,
                            )
                        ]
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"]) * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ],
                    )
                    Story.append(t1)
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s><b>FROM:</b> %s</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    (booking["pu_Contact_F_L_Name"])
                                    if (booking["pu_Contact_F_L_Name"])
                                    else "",
                                ),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>%s %s</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    str(booking["pu_Address_Street_1"])
                                    if booking["pu_Address_Street_1"]
                                    else "",
                                    str(booking["pu_Address_Street_2"])
                                    if booking["pu_Address_Street_2"]
                                    else "",
                                ),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>%s %s</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    str(booking["pu_Address_Suburb"])
                                    if booking["pu_Address_Suburb"]
                                    else "",
                                    str(booking["pu_Address_PostalCode"])
                                    if booking["pu_Address_PostalCode"]
                                    else "",
                                ),
                                style_left,
                            )
                        ],
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (2 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ],
                    )

                    tbl_data2 = [
                        [
                            Paragraph(
                                "<font size=%s>Items: %s</font>"
                                % (label_settings["font_size_medium"], totalQty),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>Weight: %s KG</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    booking_line["e_Total_KG_weight"]
                                    if booking_line["e_Total_KG_weight"]
                                    else "N/A",
                                ),
                                style_left,
                            )
                        ],
                        [
                            Paragraph(
                                "<font size=%s>Cube: %s M3</font>"
                                % (
                                    label_settings["font_size_medium"],
                                    booking_line["e_1_Total_dimCubicMeter"]
                                    if booking_line["e_1_Total_dimCubicMeter"]
                                    else "N/A",
                                ),
                                style_left,
                            )
                        ],
                    ]

                    t2 = Table(
                        tbl_data2,
                        colWidths=(
                            float(label_settings["label_image_size_length"])
                            * (1 / 3)
                            * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ],
                    )

                    data = [[t1, t2]]

                    t1_w = (
                        float(label_settings["label_image_size_length"]) * (2 / 3) * mm
                    )
                    t2_w = (
                        float(label_settings["label_image_size_length"]) * (1 / 3) * mm
                    )

                    shell_table = Table(
                        data,
                        colWidths=[t1_w, t2_w],
                        style=[
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            # ('SPAN',(0,0),(0,-1)),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ],
                    )

                    Story.append(shell_table)
                    Story.append(Spacer(1, 15))
                    Story.append(hr)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s>Delivery:</font>"
                                % (label_settings["font_size_small"]),
                                style_left,
                            )
                        ]
                    ]

                    t1 = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"]) * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ],
                    )

                    Story.append(t1)

                    barcode = (
                        booking["v_FPBookingNumber"]
                        + "DESC"
                        + str(k + 1).zfill(10)
                        + booking["de_To_Address_PostalCode"]
                    )

                    tbl_data = [
                        [
                            code128.Code128(
                                barcode,
                                barHeight=15 * mm,
                                barWidth=0.7,
                                humanReadable=True,
                            )
                        ]
                    ]

                    t1 = Table(
                        tbl_data,
                        colWidths=(
                            (float(label_settings["label_image_size_length"])) * mm
                        ),
                        style=[
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (0, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LEFTPADDING", (0, 0), (0, -1), 0),
                            ("RIGHTPADDING", (0, 0), (0, -1), 0),
                            # ('BOX', (0, 0), (-1, -1), 1, colors.black)
                        ],
                    )

                    Story.append(t1)
                    Story.append(Spacer(1, 5))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s>%s of %s</font>"
                                % (label_settings["font_size_small"], j, totalQty),
                                style_center,
                            )
                        ]
                    ]

                    shell_table = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"]) * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ],
                    )

                    Story.append(shell_table)
                    Story.append(Spacer(1, 10))

                    tbl_data1 = [
                        [
                            Paragraph(
                                "<font size=%s color=%s >%s</font>"
                                % (
                                    label_settings["font_size_small"],
                                    colors.white,
                                    "Powerd by DeliverMe Learn more at Deliverme.com",
                                ),
                                style_center,
                            )
                        ]
                    ]

                    shell_table = Table(
                        tbl_data1,
                        colWidths=(
                            float(label_settings["label_image_size_length"]) * mm
                        ),
                        style=[
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                        ],
                    )
                    Story.append(shell_table)

                    Story.append(PageBreak())

                    j += 1

            i += 1

            # doc.build(Story)
            doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)
            # end writting data into pdf file
            file.close()
        # end loop through data fetched from dme_bookings table

    except Exception as e:
        print("Error1: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(dir(exc_type), fname, exc_tb.tb_lineno)
        # print("Error: unable to fecth data")

    print("#901 - Finished %s\n\n\n" % datetime.datetime.now())
    mysqlcon.close()
