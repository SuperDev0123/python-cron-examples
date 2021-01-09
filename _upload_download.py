import os
import pysftp
import shutil


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
                    print("@104 - downloading: ", file)
                    sftp_con.get(sftp_filepath + file, local_filepath + file)
                    sftp_file_size = sftp_con.lstat(sftp_filepath + file).st_size
                    local_file_size = os.stat(local_filepath + file).st_size

                    if sftp_file_size == local_file_size:  # Check file size
                        print("@105 - Download success: " + file)
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
