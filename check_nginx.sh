#!/bin/bash
function check_process(){
	# check the args
	if [ "$1" = "" ]; then
		return 0
        fi
  #PROCESS_NUM => get the process number regarding the given thread name
  PROCESS_NUM=$(ps -ef | grep "$1" | grep -v "grep" | wc -l)
 # | grep -v "grep" | wc -l
        # for degbuging...

	if [[ $PROCESS_NUM -gt 0 ]];
	then
		return 1	
	else
		return 0
	fi
}

check_process "runserver 8080" # the thread name
CHECK_RET=$?
if [ $CHECK_RET -eq 0 ]; # none exist
then
	#bash /opt/chrons/nginx.sh
	echo "not running"
	/bin/bash /opt/chrons/nginx.sh
else
	echo "nginx running"
fi
