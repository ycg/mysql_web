#! /bin/bash

#注意如果SQL比较长需要修改sample字段为mediumtext

#1.general_log存放的数据库地址
db_host=""
db_port=3306
db_user=""
db_password=""
db_database="db1"

#2.读取general_log的数据库地址
mysql_client="/usr/local/mysql/bin/mysql"
mysql_host=""
mysql_port=3306
mysql_user=""
mysql_password=""

general_log_dir="/general_log/"
pt_query_digest="/usr/bin/pt-query-digest"

function start_general_log()
{
	general_log_file_path=$general_log_dir`date "+%Y-%m-%d_%H-%M-%S.slow"`
	`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password \
	-e "set global general_log = 1;set global log_output = 'FILE';set global general_log_file = '$general_log_file_path';"`
}

function stop_general_log()
{
	`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "set global general_log = 0;"`
}

function check_general_log()
{
	general_log_file=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "show global variables like 'general_log_file';" | grep log | awk '{print $2}'`
	echo "$general_log_file"
	$pt_query_digest --type=genlog \
	--user=$db_user --password=$db_password --port=$db_port --charset=utf8 \
	--review h=$db_host,D=$db_database,t=general_log_review  \
	--history h=$db_host,D=$db_database,t=general_log_review_history  \
	--no-report --limit=100% \
	--filter='$event->{fingerprint} =~ m/^select/i' $general_log_file > /tmp/general_log.log
	#--filter=" \$event->{add_column} = length(\$event->{arg})" $general_log_file > /tmp/general_log.log

	if [ -f "$general_log_file" ]; then
	    rm "$general_log_file"
	fi
}

if [ ! -d "$general_log_dir" ]; then
	mkdir "$general_log_dir"
fi

while true
do
    echo "------------start general log-------------"
    start_general_log
    sleep 1m
    echo "<<<<<<<<<<<stop general log>>>>>>>>>>>>>>>"
    stop_general_log
    check_general_log
    echo "==============check ok===================="
    sleep 10
done


