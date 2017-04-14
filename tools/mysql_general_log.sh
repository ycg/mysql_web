#! /bin/bash

#注意如果SQL比较长需要修改sample字段为mediumtext
#ALTER TABLE `db1`.`general_log_review` ADD COLUMN `is_reviewed` TINYINT UNSIGNED NOT NULL DEFAULT 0;

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
    general_log_file_old=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "show global variables like 'general_log_file';" | grep log | awk '{print $2}'`
    echo "---------------------------------start general log-------------------------------------------------"
	general_log_file_new=$general_log_dir`date "+%Y-%m-%d_%H-%M-%S.slow"`
	`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password \
	-e "set global general_log = 1;set global log_output = 'FILE';set global general_log_file = '$general_log_file_new';"`

    sleep 1
	if [ -f "$general_log_file_old" ]; then
	    rm -rf "$general_log_file_old"
	    echo "remove $general_log_file_old ok."
	fi
}

function stop_general_log()
{
    echo "===================================stop general ok==================================================="
	`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "set global general_log = 0;"`
}

function check_general_log()
{
	echo "----------------------------------check general log------------------------------------------------"
	general_log_file=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "show global variables like 'general_log_file';" | grep log | awk '{print $2}'`
	$pt_query_digest --type=genlog \
	--user=$db_user --password=$db_password --port=$db_port --charset=utf8 \
	--review h=$db_host,D=$db_database,t=general_log_review  \
	--history h=$db_host,D=$db_database,t=general_log_review_history  \
	--no-report --limit=100% \
	--filter='$event->{fingerprint} =~ m/^select/i' $general_log_file > /tmp/general_log.log
	echo "---------------------------------------check ok----------------------------------------------------"
	echo ""
}

if [ ! -d "$general_log_dir" ]; then
	mkdir "$general_log_dir"
fi

while true
do
    start_general_log
    sleep 1m
    stop_general_log
    check_general_log
    sleep 10
done


