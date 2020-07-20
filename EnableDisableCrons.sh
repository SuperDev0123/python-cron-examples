#!/bin/bash
arr=("MoveSuccess2ToBookings", "TransferBookings", "TruncateBookings", "TransferBookingRelated", "TruncateBookingRelated")

for i in "${arr[@]}"
do
        cronstatus=$(mysql dme_db_prod --host=deliverme-db.cgc7xojhvzjl.ap-southeast-2.rds.amazonaws.com --user=fmadmin --password=oU8pPQxh -se "Select option_value from dme_options where option_n$

        if [ "1" = "$cronstatus" ]; then
                crontab -l | sed "/^#.*$i/s/^#//" | crontab -   
        else
                crontab -l | sed "/^[^#].*$i/s/^/#/" | crontab -
        fi

done

crontab -l
