# Python 3.7.0

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil

import _status_history
from _env import (
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_PORT,
    DB_NAME,
    ST_FTP_DIR as FTP_DIR,
    ST_ARCHIVE_FTP_DIR as ARCHIVE_FTP_DIR,
    ST_CSV_DIR as CSV_DIR,
    ST_ARCHIVE_CSV_DIR as ARCHIVE_CSV_DIR,
)
from _options_lib import get_option, set_option
from _upload_download import download_sftp, upload_sftp

# sftp server infos
sftp_server_infos = {
    "st": {
        "type": "Freight Provider",
        "name": "StarTrack",
        "host": "ftp3.startrackexpress.com.au",
        "username": "deliver_me",
        "password": "3rp2NcHS",
        "sftp_filepath": "/Tracking/",
        "local_filepath": FTP_DIR,
        "local_filepath_archive": ARCHIVE_FTP_DIR,
    },
    "biopak": {
        "type": "Client",
        "name": "BIOPAK",
        "host": "ftp.biopak.com.au",
        "username": "dme_biopak",
        "password": "3rp2NcHS",
        "sftp_filepath": "/DME/POD/",
        "local_filepath": CSV_DIR,
        "local_filepath_archive": ARCHIVE_CSV_DIR,
    },
}


type_flag_transit_state = {
    "B": {
        "transit_state": "BOOK-IN. DELIVERY DUE",
        "detail": "Consignment booked into the warehouse with a confirmed updated ETA Date",
    },
    "D": {
        "transit_state": "DELIVERED",
        "detail": "Consignment has been successfully delivered",
    },
    "C": {
        "transit_state": "DELIVERED BUT QC’D LATE OR UNSERVICABLE",
        "detail": "Consignment has been delivered but flagged as late or unserviceable",
    },
    "H": {
        "transit_state": "HELD. AWAITING INSTRUCTIONS FROM SENDER.",
        "detail": "Consignment has been held at the StarTrack Depot",
    },
    "M": {
        "transit_state": "# ITEMS ON BOARD FOR DELIVERY.",
        "detail": "Consignment is on-board for delivery with the StarTrack Driver",
    },
    "N": {"transit_state": "SCANNED IN TRANSIT (NEW ZEALAND)", "detail": ""},
    "R": {
        "transit_state": "RETURNED TO DELIVERY DEPOT.",
        "detail": "Consignment has been Returned to the Delivery Depot - usually after an Attempted Delivery",
    },
    "S": {
        "transit_state": "SHORTAGE. # ITEM MISSING AT DELIVERY DEPOT",
        "detail": "Consignment has been delivered, however not all pieces were delivered",
    },
    "X": {"transit_state": "RECONSIGNED", "detail": "Consignment has been reconsigned"},
    "Y": {
        "transit_state": "RETURN TO SENDER",
        "detail": "Consignment has been identified for Return To Sender",
    },
    "L": {
        "transit_state": "LABELS IN TRANSIT",
        "detail": "Items have been scanned at a StarTrack location - this may be at the origin or destination depot.",
    },
    "G": {
        "transit_state": "REFUSED DELIVERY, PENDING FUTHER INSTRUCTIONS FROM",
        "detail": "Receiver has refused delivery of the Consignment",
    },
    "V": {
        "transit_state": "REDELIVER",
        "detail": "Consignment has had a previous Delivery Attempt and a new delivery date has been confirmed with the receiver",
    },
    "F": {
        "transit_state": "FINAL SHORTAGE",
        "detail": "Consignment was not delivered in full and missing items have not been located - usually occurs approx. 5 days after delivery after all attempts have been made to locate missing items",
    },
    "P": {
        "transit_state": "PICKED UP",
        "detail": "Consignment has received a Pickup Scan at the Pickup Location",
    },
    "T": {"transit_state": "POD RETURNED TO DEPOT", "detail": ""},
    "Z": {
        "transit_state": "CONSIGNMENT REGISTERED AS A BOOKIN",
        "detail": "Consignment booked into the warehouse without any changes to the ETA Date",
    },
    "O": {
        "transit_state": "POD FILED",
        "detail": "Confirmation a delivery has been completed, this may be the only record received in regional locations where no scanning equipment available",
    },
    "I": {
        "transit_state": "CONSIGNMENT NOTE SCANNED IN TRANSIT",
        "detail": "Consignment has been scanned at a StarTrack location - this may be at the origin or destination depot.",
    },
    "Q": {
        "transit_state": "TRUCK PROOF OF PICKUP (TRUCK OUT)",
        "detail": "Confirmation that StarTrack has taken custody of the consignment from the customer",
    },
    "W": {
        "transit_state": "TRANSFER TO ANOTHER DRIVER (BREAKDOWN, ACCIDENT, MANIFESTED IN ERROR)",
        "detail": "Consignment was transferred to another driver due to a break down, accident or a manifesting error",
    },
    "1": {
        "transit_state": "INCORRECT ADDRESS",
        "detail": "Consignment has been returned to the Delivery Depot as the delivery address is invalid",
    },
    "2": {
        "transit_state": "ATTEMPTED DELIVERY",
        "detail": "Consignment has been returned to the Delivery Depot as the receiver was not home or closed",
    },
    "3": {
        "transit_state": "DELIVERED TO POSTOFFICE",
        "detail": "Consignment has been delivered to a postoffice for collection by the receiver",
    },
}

error_receiver_signature_fields = [
    "NHCL",
    "CLOSED",
    "CHECK ADDRESS",
    "REFUSED DELIV",
    "OTHER RETURN",
    "RETURN TO DEPOT",
    "LAI",
    "ATL",
    "AUTHORITY TO LEAVE",
]


def get_booking(consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `b_bookingID_Visual`, `pk_booking_id`, `b_status`, `b_status_API` \
                From `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (consignment_number))
        booking = cursor.fetchone()

        return booking


def get_translations(mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `dme_status`, `fp_original_status`, `fp_lookup_status` \
            FROM `dme_utl_fp_statuses` \
            WHERE `fp_name`=%s"
        cursor.execute(sql, ("Startrack"))
        translations = cursor.fetchall()

        return translations


def get_dme_status_from_flag(translations, type_flag):
    for translation in translations:
        if translation["fp_lookup_status"] == type_flag:
            return translation["dme_status"]

    return ""


def csv_write(fpath, f, mysqlcon):
    # Write Header
    f.write(
        "consignment_number, date_of_event, fp_status_code, fp_status, fp_status_details, dme_status, pod_name, reason, cartons_delivered"
    )
    with mysqlcon.cursor() as cursor:
        translations = get_translations(mysqlcon)

        try:
            with open(fpath) as ftp_file:
                for line in ftp_file:
                    consignment_number = line.split(",")[0].strip()
                    b_del_to_signed_time = datetime.datetime.strptime(
                        line.split(",")[1].strip(), "%Y%m%d%H%M"
                    )
                    b_del_to_signed_name = line.split(",")[2].strip()
                    type_flag = line.split(",")[3].strip()
                    transit_state = type_flag_transit_state[type_flag]["transit_state"]
                    detail = type_flag_transit_state[type_flag]["detail"]
                    dme_status = get_dme_status_from_flag(translations, type_flag)
                    cartons_delivered = int(line.split(",")[11].strip())

                    print(
                        "@200 - ",
                        consignment_number,
                        b_del_to_signed_time,
                        b_del_to_signed_name,
                        type_flag,
                        transit_state,
                        dme_status,
                        cartons_delivered,
                    )

                    booking = get_booking(consignment_number, mysqlcon)
                    if booking:
                        # If new status, create status_history
                        if booking["b_status"] != dme_status:
                            print("@201 - New Status!", booking["b_status"], dme_status)
                            _status_history.create(
                                booking["id"], None, datetime.datetime.now(), dme_status
                            )

                        sql = "UPDATE `dme_bookings` \
                            SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s, b_status=%s \
                            WHERE `v_FPBookingNumber`=%s"
                        cursor.execute(
                            sql,
                            (
                                b_del_to_signed_name,
                                b_del_to_signed_time,
                                datetime.datetime.now(),
                                transit_state,
                                dme_status,
                                consignment_number,
                            ),
                        )
                        mysqlcon.commit()

                    # Write Each Line
                    comma = ","
                    newLine = "\n"
                    eachLineText = consignment_number + comma
                    eachLineText += b_del_to_signed_time.strftime("%Y%m%d") + comma
                    eachLineText += type_flag + comma
                    eachLineText += transit_state + comma
                    eachLineText += detail + comma
                    eachLineText += dme_status + comma
                    eachLineText += b_del_to_signed_name + comma
                    eachLineText += "" + comma
                    eachLineText += str(cartons_delivered) + comma

                    f.write(newLine + eachLineText)
        except Exception as e:
            print("@204 - ", str(e))
            traceback.print_exc()
            exit(1)


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())
    time1 = time.time()

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

    if not os.path.isdir(FTP_DIR) or not os.path.isdir(CSV_DIR):
        print('Given argument "%s, %s" is not a directory' % FTP_DIR, CSV_DIR)
        exit(1)

    try:
        option = get_option(mysqlcon, "st_status_pod")

        if int(option["option_value"]) == 0:
            print("#905 - `st_status_pod` option is OFF")
        elif option["is_running"]:
            print("#905 - `st_status_pod` script is already RUNNING")
        else:
            print("#906 - `st_status_pod` option is ON")
            set_option(mysqlcon, "st_status_pod", True)
            print("#910 - Processing...")

            # Download .FTP files
            try:
                download_sftp(
                    sftp_server_infos["st"]["host"],
                    sftp_server_infos["st"]["username"],
                    sftp_server_infos["st"]["password"],
                    sftp_server_infos["st"]["sftp_filepath"],
                    sftp_server_infos["st"]["local_filepath"],
                    sftp_server_infos["st"]["local_filepath_archive"],
                )
            except OSError as e:
                print("Failed download .FTP files from remote. Error: ", str(e))
                set_option(mysqlcon, "st_status_pod", False, time1)

            try:
                for fname in sorted(os.listdir(FTP_DIR)):
                    fpath = os.path.join(FTP_DIR, fname)

                    if os.path.isfile(fpath) and fname.endswith(".FTP"):
                        print("@100 Detect .FTP file:", fpath)
                        csv_name = (
                            str(datetime.datetime.now().strftime("%d-%m-%Y__%H_%M_%S"))
                            + ".csv"
                        )
                        f = open(CSV_DIR + csv_name, "w")
                        csv_write(fpath, f, mysqlcon)
                        f.close()

                        # Download .csv file
                        upload_sftp(
                            sftp_server_infos["biopak"]["host"],
                            sftp_server_infos["biopak"]["username"],
                            sftp_server_infos["biopak"]["password"],
                            sftp_server_infos["biopak"]["sftp_filepath"],
                            sftp_server_infos["biopak"]["local_filepath"],
                            sftp_server_infos["biopak"]["local_filepath_archive"],
                            csv_name,
                        )

                        shutil.move(FTP_DIR + fname, ARCHIVE_FTP_DIR + fname)
                        print("@109 Moved .FTP file:", fpath)

                set_option(mysqlcon, "st_status_pod", False, time1)
            except OSError as e:
                print(str(e))
                set_option(mysqlcon, "st_status_pod", False, time1)
    except Exception as e:
        print("Error 904:", str(e))
        set_option(mysqlcon, "st_status_pod", False, time1)

    mysqlcon.close()
    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())
