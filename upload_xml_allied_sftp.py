# Python 3.6.6

import sys, time
import os
import errno
from datetime import datetime
import uuid
import urllib, requests
import json
import pymysql, pymysql.cursors
import base64
import shutil
import pysftp

production = True  # Dev
# production = False # Local

# start check if xmls folder exists
if production:
    local_filepath = "/opt/s3_private/xmls/allied_au/"
    local_filepath_dup = (
        "/opt/s3_private/xmls/allied_au/archive/"
        + str(datetime.now().strftime("%Y_%m_%d"))
        + "/"
    )
else:
    local_filepath = "/Users/admin/work/goldmine/dme_api/static/xmls/allied_au/"
    local_filepath_dup = (
        "/Users/admin/work/goldmine/dme_api/static/xmls/allied_au/archive/"
        + str(datetime.now().strftime("%Y_%m_%d"))
        + "/"
    )

if not os.path.exists(local_filepath):
    os.makedirs(local_filepath)
# end check if xmls folder exists


def upload_sftp(fname, fpath):
    sftp_filepath = "/home/NSW/delvme.external/indata/"
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(
        host="edi.alliedexpress.com.au",
        username="delvme.external",
        password="987899e64",
        cnopts=cnopts,
    ) as sftp_con:
        with sftp_con.cd(sftp_filepath):
            sftp_con.put(local_filepath + fname)
            sftp_file_size = sftp_con.lstat(sftp_filepath + fname).st_size
            local_file_size = os.stat(local_filepath + fname).st_size

            if sftp_file_size == local_file_size:
                if not os.path.exists(local_filepath_dup):
                    os.makedirs(local_filepath_dup)
                shutil.move(local_filepath + fname, local_filepath_dup + fname)
                print("@109 Moved xml file:", fpath)

        sftp_con.close()


if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())

    try:
        for fname in os.listdir(local_filepath):
            fpath = os.path.join(local_filepath, fname)

            if os.path.isfile(fpath) and fname.endswith(".xml"):
                print("@100 Detect xml file:", fpath)
                upload_sftp(fname, fpath)

    except OSError as e:
        print(str(e))

    print("#999 - Finished %s\n\n\n" % datetime.datetime.now())

