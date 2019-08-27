# Python 3.6.6

import sys, time
import os
import datetime
import pymysql, pymysql.cursors
import shutil
import glob
import ntpath

if __name__ == "__main__":
    print("#900 - Running %s" % datetime.datetime.now())

    source_url = "/Users/admin/work/goldmine/scripts/dir01/"

    for file in glob.glob(os.path.join(source_url, "*.pdf")):
        filename = ntpath.basename(file)
        new_filename = filename.split("_")[2]
        print(filename, "-", new_filename)
        shutil.move(source_url + filename, source_url + new_filename)

    print("#901 - Finished %s" % datetime.datetime.now())
