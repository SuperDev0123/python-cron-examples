
cronstatus=$(mysql dme_db_dev --host=deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh -se "Select option_value from dme_options where option_name='TransferBookingRelated'")

if [ "0" = "$cronstatus" ]; then
	echo 'no need to run'
else
	echo 'Starting process'


mysql --host=deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh --database=dme_db_dev --execute="CALL TransferBooking_Related;"

cronstatus=$(mysql dme_db_dev --host=deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh -se "Update dme_options set start_time=SYSDATE(), end_time=sysdate(), start_count=0, end_count = (SELECT count(*) FROM dme_bookings WHERE LOWER(vx_freight_provider)= 'cope' ), option_value=0 where option_name='TransferBookingRelated'")

fi
