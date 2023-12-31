EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "bookings@deliver-me.com.au"
EMAIL_HOST_PASSWORD = "Dme35718&*"

# **************
# **  LOCAL   **
# **************

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_PORT = 3306
DB_NAME = "deliver_me"

API_URL = "http://localhost:8000/api"  # Local
USERNAME = "dme"
PASSWORD = "password#123"

# SI - Sharepoint import
SI_DOWNLOAD_DIR = "./xls/downloaded"
SI_IMPORT_DIR = "./xls/imported"
SI_ERROR_DIR = "./xls/issued"

# ST - Startrack
ST_FTP_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
ST_ARCHIVE_FTP_DIR = "/Users/admin/work/goldmine/scripts/dir02/"
ST_CSV_DIR = "/Users/admin/work/goldmine/scripts/dir01/"
ST_ARCHIVE_CSV_DIR = "/Users/admin/work/goldmine/scripts/dir02/"

# PO - Pricing Only
PO_RESULT_DIR = "./../dir02/"
PO_SRC_DIR = "./../dir01/"
PO_SRC_INPROGRESS_DIR = "./../dme_api/static/uploaded/pricing_only/inprogress/"
PO_SRC_ACHIEVE_DIR = "./../dme_api/static/uploaded/pricing_only/achieve/"

# PR - Pricing Rule
PR_RESULT_DIR = "./../dme_api/static/uploaded/pricing_rule/result/"
PR_SRC_DIR = "./../dme_api/static/uploaded/pricing_rule/indata/"
PR_SRC_INPROGRESS_DIR = "./../dme_api/static/uploaded/pricing_rule/inprogress/"
PR_SRC_ACHIEVE_DIR = "./../dme_api/static/uploaded/pricing_rule/achieve/"


# **************
# ***  DEV   ***
# **************

# DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
# DB_USER = "fmadmin"
# DB_PASS = "oU8pPQxh"
# DB_PORT = 3306
# DB_NAME = "dme_db_dev"  # Dev

# API_URL = "http://3.105.62.128/api"  # Dev
# USERNAME = "dme"
# PASSWORD = "pass#123"

# SI - Sharepoint import
# SI_DOWNLOAD_DIR = "/opt/chrons/xls/downloaded"
# SI_IMPORT_DIR = "/opt/chrons/xls/imported"
# SI_ERROR_DIR = "/opt/chrons/xls/issued"

# ST - Startrack
# ST_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/indata/"
# ST_ARCHIVE_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/archive/"
# ST_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/indata/"
# ST_ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/archive/"

# PO - Pricing Only
# PO_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/result/"
# PO_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/indata/"
# PO_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/inprogress/"
# PO_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/achieve/"

# PR - Pricing Rule
# PR_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/result/"
# PR_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/indata/"
# PR_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/inprogress/"
# PR_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/achieve/"


# **************
# ***  PROD  ***
# **************

# DB_HOST = "deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
# DB_USER = "fmadmin"
# DB_PASS = "oU8pPQxh"
# DB_PORT = 3306
# DB_NAME = "dme_db_prod"  # Prod

# API_URL = "http://13.55.64.102/api"  # Prod

# ST - Startrack
# ST_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/indata/"
# ST_ARCHIVE_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/archive/"
# ST_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/indata/"
# ST_ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/archive/"

# PO - Pricing Only
# PO_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/result/"
# PO_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/indata/"
# PO_SRC_INPROGRESS_DIR = (
#     "/var/www/html/dme_api/static/uploaded/pricing_only/inprogress/"
# )
# PO_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/achieve/"

# PR - Pricing Rule
# PR_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/result/"
# PR_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/indata/"
# PR_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/inprogress/"
# PR_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/achieve/"
