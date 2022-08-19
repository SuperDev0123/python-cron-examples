
cronstatus=$(mysql dme_db_dev --host=deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh -se "Select option_value from dme_options where option_name='TruncateBookings'")

if [ "0" = "$cronstatus" ]; then
	echo 'no need to run'
else
	echo 'Starting process'


mysql --host=deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh --database=dme_db_dev --execute="CALL TruncateBookings;"

cronstatus=$(mysql dme_db_dev --host=deliverme-db8.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh -se "Update dme_options set option_value=0 where option_name='TruncateBookings'")

fi
