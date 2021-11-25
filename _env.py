EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "bookings@deliver-me.com.au"
EMAIL_HOST_PASSWORD = "Dme35718&*"


# **************
# **  LOCAL   **
# **************

# DB_NAME="dme_db_prod"
# DB_USER="fmadmin"
# DB_PASS="oU8pPQxh"
# DB_HOST="deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
# DB_PORT=3306

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_PORT = 3306
DB_NAME = "deliver_me"

API_URL = "http://localhost:8000/api"  # Local
USERNAME = "dme"
PASSWORD = "LRyuNp3zn[XE_`8-"

# S3 URL
S3_URL="https://dme-pod-api-static.s3-ap-southeast-2.amazonaws.com"

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
PO_RESULT_DIR = "./../dme_api/static/uploaded/pricing_only/result/"
PO_SRC_DIR = "./../dme_api/static/uploaded/pricing_only/indata/"
PO_SRC_INPROGRESS_DIR = "./../dme_api/static/uploaded/pricing_only/inprogress/"
PO_SRC_ACHIEVE_DIR = "./../dme_api/static/uploaded/pricing_only/achieve/"

# PR - Pricing Rule
PR_RESULT_DIR = "./../dme_api/static/uploaded/pricing_rule/result/"
PR_SRC_DIR = "./../dme_api/static/uploaded/pricing_rule/indata/"
PR_SRC_INPROGRESS_DIR = "./../dme_api/static/uploaded/pricing_rule/inprogress/"
PR_SRC_ACHIEVE_DIR = "./../dme_api/static/uploaded/pricing_rule/achieve/"

# SAPB1 - CSV INPUT
SAPB1_CSV_INPUT_DIR = "./dir01/"
SAPB1_CSV_INPUT_ACHIEVE_DIR = "./dir02/"

# HTC - Hunter Tracking CSV Input
HTC_REMOTE_DIR = "/tracking/indata/"
HTC_LOCAL_DIR = "./dir01/"

# STTCO - State Transport CSV Output (For BOOK)
STTCO_DIR = "./dir01/"
STTCO_ARCHIVE_DIR = "./dir02/"

# CCO - Century CSV Output (For BOOK)
CCO_DIR = "./dir01/"
CCO_ARCHIVE_DIR = "./dir02/"

# CENTURY TRACKING CSV
CTC_INPROGRESS_DIR = "./dme_sftp/century_au/status_csv/inprogress/"
CTC_ARCHIVE_DIR = "./dme_sftp/century_au/status_csv/archive/"
CTC_ISSUED_DIR = "./dme_sftp/century_au/status_csv/issued/"

# HUNTER TRACKING CSV
HT_INPROGRESS_DIR = "./dme_sftp/hunter_au/status_csv/inprogress/"
HT_ARCHIVE_DIR = "./dme_sftp/hunter_au/status_csv/archive/"
HT_ISSUED_DIR = "./dme_sftp/hunter_au/status_csv/issued/"

# **************
# ***  DEV   ***
# **************

# DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
# DB_USER = "fmadmin"
# DB_PASS = "oU8pPQxh"
# DB_PORT = 3306
# DB_NAME = "dme_db_dev"  # Dev

# API_URL = "http://3.105.62.128/api"  # Dev
# USERNAME = "dme"
# PASSWORD = "LRyuNp3zn[XE_`8-"

# # SI - Sharepoint import
# SI_DOWNLOAD_DIR = "/opt/chrons/xls/downloaded"
# SI_IMPORT_DIR = "/opt/chrons/xls/imported"
# SI_ERROR_DIR = "/opt/chrons/xls/issued"

# # ST - Startrack
# ST_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/indata/"
# ST_ARCHIVE_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/archive/"
# ST_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/indata/"
# ST_ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/archive/"

# # PO - Pricing Only
# PO_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/result/"
# PO_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/indata/"
# PO_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/inprogress/"
# PO_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/achieve/"

# # PR - Pricing Rule
# PR_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/result/"
# PR_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/indata/"
# PR_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/inprogress/"
# PR_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/achieve/"

# # SAPB1 - CSV INPUT
# SAPB1_CSV_INPUT_DIR = "/dme_sftp/sapb1/order_transaction_csvs/indata/"
# SAPB1_CSV_INPUT_ACHIEVE_DIR = "/dme_sftp/sapb1/order_transaction_csvs/processed/"

# # HTC - Hunter Tracking CSV Input
# HTC_REMOTE_DIR = "/tracking/indata/"
# HTC_LOCAL_DIR = "/dme_sftp/hunter/tracking/csv/indata/"

# # STTCO - State Transport CSV Output (For BOOK)
# STTCO_DIR = "./dme_sftp/state_transport/book/csv/outdata/"
# STTCO_ARCHIVE_DIR = "./dme_sftp/state_transport/book/csv/archive/"

# # CCO - Century CSV Output (For BOOK)
# CCO_DIR = "./dme_sftp/century/book_csv/outdata/"
# CCO_ARCHIVE_DIR = "./dme_sftp/century/book_csv/archive/"

# # CENTURY
# CENTURY_FTP_DIR = "./dme_sftp/century_au/status_csv/inprogress/"
# CENTURY_ARCHIVE_FTP_DIR = "./dme_sftp/century_au/status_csv/archive/"
# CENTURY_ISSUED_FTP_DIR = "./dme_sftp/century_au/status_csv/issued/"

# **************
# ***  PROD  ***
# **************

# DB_HOST = "deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com"
# DB_USER = "fmadmin"
# DB_PASS = "oU8pPQxh"
# DB_PORT = 3306
# DB_NAME = "dme_db_prod"  # Prod

# API_URL = "http://13.55.64.102/api"  # Prod
# USERNAME = "dme"
# PASSWORD = "LRyuNp3zn[XE_`8-"

# # SI - Sharepoint import
# SI_DOWNLOAD_DIR = "/opt/chrons/xls/downloaded"
# SI_IMPORT_DIR = "/opt/chrons/xls/imported"
# SI_ERROR_DIR = "/opt/chrons/xls/issued"

# # ST - Startrack
# ST_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/indata/"
# ST_ARCHIVE_FTP_DIR = "/home/cope_au/dme_sftp/startrack_au/ftp/archive/"
# ST_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/indata/"
# ST_ARCHIVE_CSV_DIR = "/home/cope_au/dme_sftp/startrack_au/pickup_ext/archive/"

# # PO - Pricing Only
# PO_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/result/"
# PO_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/indata/"
# PO_SRC_INPROGRESS_DIR = (
#     "/var/www/html/dme_api/static/uploaded/pricing_only/inprogress/"
# )
# PO_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_only/achieve/"

# # PR - Pricing Rule
# PR_RESULT_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/result/"
# PR_SRC_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/indata/"
# PR_SRC_INPROGRESS_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/inprogress/"
# PR_SRC_ACHIEVE_DIR = "/var/www/html/dme_api/static/uploaded/pricing_rule/achieve/"

# # SAPB1 - CSV INPUT
# SAPB1_CSV_INPUT_DIR = "/dme_sftp/sapb1/order_transaction_csvs/indata/"
# SAPB1_CSV_INPUT_ACHIEVE_DIR = "/dme_sftp/sapb1/order_transaction_csvs/processed/"

# # HTC - Hunter Tracking CSV Input
# HTC_REMOTE_DIR = "/tracking/indata/"
# HTC_LOCAL_DIR = "/dme_sftp/hunter/tracking/csv/indata/"

# # STTCO - State Transport CSV Output (For BOOK)
# STTCO_DIR = "./dme_sftp/state_transport/book/csv/outdata/"
# STTCO_ARCHIVE_DIR = "./dme_sftp/state_transport/book/csv/archive/"

# # CCO - Century CSV Output (For BOOK)
# CCO_DIR = "/dme_sftp/century_au/book_csv/outdata/"
# CCO_ARCHIVE_DIR = "/dme_sftp/century_au/book_csv/archive/"

# # CTC - CENTURY Tracking CSV
# CTC_INPROGRESS_DIR = "/dme_sftp/century_au/status_csv/inprogress/"
# CTC_ARCHIVE_DIR = "/dme_sftp/century_au/status_csv/archive/"
# CTC_ISSUED_DIR = "/dme_sftp/century_au/status_csv/issued/"
