# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import pysftp

IS_DEBUG = False
IS_PRODUCTION = True  # Dev
# IS_PRODUCTION = False  # Local

if IS_PRODUCTION:
    DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
    DB_USER = "fmadmin"
    DB_PASS = "oU8pPQxh"
    DB_PORT = 3306
    # DB_NAME = 'dme_db_dev'  # Dev
    DB_NAME = "dme_db_prod"  # Prod
else:
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
    DB_NAME = "deliver_me"

if IS_PRODUCTION:
    FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/indata/"
    ARCHIVE_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/archive/"
    CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/indata/"
    ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/archive/"
else:
    FTP_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
    ARCHIVE_FTP_DIR = "/Users/admin/work/goldmine/scripts/dir02/"
    CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
    ARCHIVE_CSV_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

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
    "B": "BOOK-IN. DELIVERY DUE",
    "D": "DELIVERED",
    "C": "DELIVERED BUT QC’D LATE OR UNSERVICABLE",
    "H": "HELD. AWAITING INSTRUCTIONS FROM SENDER.",
    "M": "# ITEMS ON BOARD FOR DELIVERY.",
    "N": "SCANNED IN TRANSIT (NEW ZEALAND)",
    "R": "RETURNED TO DELIVERY DEPOT.",
    "S": "SHORTAGE. # ITEM MISSING AT DELIVERY DEPOT",
    "X": "RECONSIGNED",
    "Y": "RETURN TO SENDER",
    "L": "LABELS IN TRANSIT",
    "G": "REFUSED DELIVERY, PENDING FUTHER INSTRUCTIONS FROM",
    "V": "REDELIVER",
    "F": "FINAL SHORTAGE",
    "P": "PICKED UP",
    "T": "POD RETURNED TO DEPOT",
    "Z": "CONSIGNMENT REGISTERED AS A BOOKIN",
    "O": "POD FILED",
    "I": "CONSIGNMENT NOTE SCANNED IN TRANSIT",
    "Q": "TRUCK PROOF OF PICKUP (TRUCK OUT)",
    "W": "TRANSFER TO ANOTHER DRIVER (BREAKDOWN, ACCIDENT, MANIFESTED IN ERROR)",
    "1": "INCORRECT ADDRESS",
    "2": "ATTEMPTED DELIVERY",
    "3": "DELIVERED TO POSTOFFICE",
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


def download_sftp(
    host, username, password, sftp_filepath, local_filepath, local_filepath_archive
):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host=host, username=username, password=password, cnopts=cnopts
    ) as sftp_con:
        print("@102 - Connected to sftp")

        with sftp_con.cd(sftp_filepath):
            print("@103 - Go to sftp dir")

            for file in sftp_con.listdir():
                lstatout = str(sftp_con.lstat(file)).split()[0]

                if "d" not in lstatout:  # If file
                    sftp_con.get(sftp_filepath + file, local_filepath + file)
                    sftp_file_size = sftp_con.lstat(sftp_filepath + file).st_size
                    local_file_size = os.stat(local_filepath + file).st_size

                    if sftp_file_size == local_file_size:  # Check file size
                        print("@104 - Download success: " + file)
                        sftp_con.remove(sftp_filepath + file)  # Delete file from remote

        sftp_con.close()


def upload_sftp(
    host,
    username,
    password,
    sftp_filepath,
    local_filepath,
    local_filepath_archive,
    filename,
):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host=host, username=username, password=password, cnopts=cnopts
    ) as sftp_con:
        print("@202 - Connected to sftp")
        with sftp_con.cd(sftp_filepath):
            print("@203 - Go to sftp dir")
            sftp_con.put(local_filepath + filename)
            sftp_file_size = sftp_con.lstat(sftp_filepath + filename).st_size
            local_file_size = os.stat(local_filepath + filename).st_size

            if sftp_file_size == local_file_size:
                print("@204 - Uploaded successfully!")
                filename_archive = filename

                if filename.endswith(".csv_"):
                    print("@205 - Renamed successfully!")
                    filename_archive = filename_archive[:-1]
                    sftp_con.rename(filename, filename_archive)

                if not os.path.exists(local_filepath_archive):
                    os.makedirs(local_filepath_archive)
                shutil.move(
                    local_filepath + filename, local_filepath_archive + filename_archive
                )
                print("@209 Moved csv file:", filename)

        sftp_con.close()


def get_booking(consignment_number, mysqlcon):
    with mysqlcon.cursor() as cursor:
        sql = "SELECT `id`, `pk_booking_id`, `b_status_API` \
                From `dme_bookings` \
                WHERE `v_FPBookingNumber`=%s"
        cursor.execute(sql, (consignment_number))
        booking = cursor.fetchone()

        return booking


def csv_write(fpath, f, mysqlcon):
    # Write Header
    f.write("consignment_number, date_of_delivery, status, pod_name, reason")
    with mysqlcon.cursor() as cursor:
        with open(fpath) as ftp_file:
            for line in ftp_file:
                consignment_number = line.split(",")[0].strip()
                booking = get_booking(consignment_number, mysqlcon)

                if booking:
                    b_del_to_signed_time = datetime.datetime.strptime(
                        line.split(",")[1].strip(), "%Y%m%d%H%M"
                    )
                    b_del_to_signed_name = line.split(",")[2].strip()
                    type_flag = line.split(",")[3].strip()

                    print(
                        "@200 - ",
                        consignment_number,
                        b_del_to_signed_time,
                        b_del_to_signed_name,
                        type_flag,
                    )

                    # sql = "UPDATE `dme_bookings` \
                    #     SET b_del_to_signed_name=%s, b_del_to_signed_time=%s, z_ModifiedTimestamp=%s, b_status_API=%s \
                    #     WHERE `v_FPBookingNumber`=%s"
                    # cursor.execute(
                    #     sql,
                    #     (
                    #         b_del_to_signed_name,
                    #         b_del_to_signed_time,
                    #         datetime.datetime.now(),
                    #         type_flag_transit_state[type_flag],
                    #         consignment_number,
                    #     ),
                    # )
                    # mysqlcon.commit()

                    # Write Each Line
                    comma = ","
                    newLine = "\n"
                    eachLineText = consignment_number + comma
                    eachLineText += b_del_to_signed_time.strftime("%Y%m%d") + comma
                    eachLineText += type_flag + comma
                    eachLineText += b_del_to_signed_name + comma

                    f.write(newLine + eachLineText)
                else:
                    print("@400: Booking not found - ", consignment_number)


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

    if not os.path.isdir(FTP_DIR) or not os.path.isdir(CSV_DIR):
        print('Given argument "%s, %s" is not a directory' % FTP_DIR, CSV_DIR)
        exit(1)

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

    try:
        for fname in sorted(os.listdir(FTP_DIR)):
            fpath = os.path.join(FTP_DIR, fname)

            if os.path.isfile(fpath) and fname.endswith(".FTP"):
                print("@100 Detect .FTP file:", fpath)
                csv_name = (
                    str(datetime.datetime.now().strftime("%d-%m-%Y__%H_%M_%S")) + ".csv"
                )
                if IS_PRODUCTION:
                    f = open(CSV_DIR + csv_name, "w")
                else:
                    f = open(CSV_DIR + csv_name, "w")
                csv_write(fpath, f, mysqlcon)
                f.close()

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

    except OSError as e:
        print(str(e))

    print("#909 - Finished %s" % datetime.datetime.now())
    mysqlcon.close()
