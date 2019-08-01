# Python 3.6.6

import os
import datetime
import shutil
import pysftp

# CSV sftp server info
host = "esmart.cope.com.au"
username = "deliverme"
password = "C3n?7u4f"
sftp_filepath = "/home/import/csvimport/upload/"
local_filepath = "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/"
local_filepath_dup = "/home/cope_au/dme_sftp/cope_au/pickup_ext/cope_au/archive/"


def upload_sftp(
    host,
    username,
    password,
    sftp_filepath,
    local_filepath,
    local_filepath_dup,
    filename,
):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host=host, username=username, password=password, cnopts=cnopts
    ) as sftp_con:
        print("@102 - Connected to sftp")
        with sftp_con.cd(sftp_filepath):
            print("@103 - Go to sftp dir")
            sftp_con.put(local_filepath + filename)
            sftp_file_size = sftp_con.lstat(sftp_filepath + filename).st_size
            local_file_size = os.stat(local_filepath + filename).st_size

            if sftp_file_size == local_file_size:
                if not os.path.exists(local_filepath_dup):
                    os.makedirs(local_filepath_dup)
                shutil.move(local_filepath + filename, local_filepath_dup + filename)
                print("@109 Moved csv file:", filename)

        sftp_con.close()


if __name__ == "__main__":
    print("#900 - Started at %s" % datetime.datetime.now())

    try:
        for fname in os.listdir(local_filepath):
            fpath = os.path.join(local_filepath, fname)

            if os.path.isfile(fpath) and fname.endswith(".csv"):
                print("@100 Detect csv file:", fpath)
                upload_sftp(
                    host,
                    username,
                    password,
                    sftp_filepath,
                    local_filepath,
                    local_filepath_dup,
                    fname,
                )

    except OSError as e:
        print(str(e))

    print("#999 - Finished at %s" % datetime.datetime.now())
