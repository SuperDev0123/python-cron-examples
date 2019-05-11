# api/cope_au_move_files_resource.py
from tastypie.resources import ModelResource
from api.models import Note
import xml.etree.ElementTree as xml
import datetime
import os
from ftplib import FTP_TLS
#from io import BytesIO
import pysftp
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
import time;
import shutil
import glob
import ntpath


class CopeAuMovePodFilesResource(ModelResource):
    class Meta:
        
        def start():
            source = "/home/cope_au/dme_sftp/cope_au/labels/indata/"
            dest = "/home/cope_au/dme_api/static/pdfs/"
            for file in glob.glob(os.path.join(source,"*.pdf")):
                shutil.copy2(file,dest)

        def copytree(source, dest, symlinks=False, ignore=None):
            for item in os.listdir(source):
                s = os.path.join(source, item)
                d = os.path.join(dest, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, symlinks, ignore)
                else:
                    shutil.copy2(s, d)

        try:
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
            
            #start ftp connection
            #try:              
                #ftp_srv = '35.162.92.135'
                #ftp_usr = 'cope_au'
                #ftp_pass = 'L/H<x7vj'

                #ftps = FTP_TLS(ftp_srv)
                #ftps.login(ftp_usr, ftp_pass)
                #ftps.prot_p() 

                #start move ftp files from one directory to another
                #source = "/home/cope_au/dme_sftp/cope_au/labels/indata/"
                #dest = "/home/cope_au/dme_api/static/pdfs/"

                #if not os.path.exists(source):
                    #print('directory not exists '+source)

                #if not os.path.exists(dest):
                    #print('directory not exists '+dest)

                #ftps.cwd(source)
                #ftps.retrlines('LIST')
                #filenames = ftps.nlst()
                #for filename in filenames:
                    #ftps.rename(source+filename, 'TEST_'+dest+filename) 
                    #sql2 = "UPDATE dme_bookings set z_label_url = %s, z_downloaded_shipping_label_timestamp = %s WHERE pk_booking_id = %s"
                    #adr2 = (filename, time.time(), booking[0], )
                    #mycursor.execute(sql2, adr2)
                #end move ftp files from one directory to another
                #ftps.quit()
            #end ftp connection

            #except Exception as e:
                #print("Error: "+str(e))          

          
            #start move server files from one directory to another
            source = "/home/cope_au/dme_sftp/cope_au/labels/indata/"
            dest = "/home/cope_au/dme_api/static/pdfs/"

            #source = "dme_sftp/cope_au/pods/indata/"
            #dest = "dme_api/static/imgs/" 

            if not os.path.exists(source):
                print('directory not exists '+source)

            if not os.path.exists(dest):
                print('directory not exists '+dest) 

            for file in glob.glob(os.path.join(source,"*.png")):  
                print(ntpath.basename(file))                    
                print(ntpath.basename(file).split('_')[2]) 
                print(ntpath.basename(file).split('_')[4].split('.')[0])  
                shutil.copy2(file, dest+'TEST_'+ntpath.basename(file))
                sql2 = "UPDATE dme_bookings set z_pod_url = %s, z_downloaded_pod_timestamp = %s WHERE b_bookingID_Visual = %s"
                adr2 = ('TEST_'+ntpath.basename(file), time.time(), ntpath.basename(file).split('_')[4].split('.')[0], )
                mycursor.execute(sql2, adr2)
            #end move server files from one directory to another                  		    

        except Exception as e:
            print("Error: "+str(e))

        queryset = Note.objects.all()
        object_class = None
        resource_name = 'movepodfiles'
        




