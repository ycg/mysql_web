#! /bin/bash

#MySQL慢查询监控脚本
#需要安装pt-tools工具包，然后把脚本设置为后台执行
#注意如果SQL比较长需要修改sample字段为mediumtext

#1.slow log存放的地址
db_host=""
db_port=3306
db_user=""
db_password=""
db_database="db1"

#2.slow log本身的地址
mysql_client="/usr/local/mysql/bin/mysql"
mysql_host=""
mysql_port=3306
mysql_user=""
mysql_password=""

#3.读取有关慢日志配置信息
slow_log_dir="/slow_log/"
slow_query_long_time=2
pt_query_digest="/usr/bin/pt-query-digest"

function check_slow_log()
{
    #获取slow log文件路径
    slow_log_file=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password \
    -e "show variables like 'slow_query_log_file';" | grep log | awk '{print $2}'`

    #设置新的slow log文件路径
    slow_log_file_path=$slow_log_dir`date "+%Y-%m-%d_%H-%M-%S.slow"`
    `$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password \
    -e "set global slow_query_log = 1;set global long_query_time=$slow_query_long_time;set global log_output='FILE';set global slow_query_log_file='$slow_log_file_path'"`

    #对旧的slow log进行解析并入库
    $pt_query_digest \
    --user=$db_user --password=$db_password --port=$db_port --charset=utf8 \
    --review h=$db_host,D=$db_database,t=mysql_slow_query_review  \
    --history h=$db_host,D=$db_database,t=mysql_slow_query_review_history  \
    --no-report --limit=100% \
    --filter=" \$event->{add_column} = length(\$event->{arg})" $slow_log_file > /tmp/slowquery.log

    echo "================check slow log [$slow_log_file] ok===================="
    if [ -f "$slow_log_file" ]; then
        rm -rf "$slow_log_file"
        echo "remove $slow_log_file ok."
    fi
}

if [ ! -d "$slow_log_dir" ]; then
    mkdir "$slow_log_dir"
fi

while true
do
    check_slow_log
    sleep 5m
done
