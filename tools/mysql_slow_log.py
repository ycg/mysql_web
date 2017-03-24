# -*- coding: utf-8 -*-

#收集慢查询shell脚本

'''
#!/bin/bash

#注意如果SQL比较常需要修改sample字段为mediumtext

#1.慢日志存放的数据库地址
db_host=""
db_port=3306
db_user=""
db_password=""
db_database="db1"

#2.读取慢日志的数据库地址
mysql_client="/usr/local/mysql/bin/mysql"
mysql_host=""
mysql_port=3306
mysql_user=""
mysql_password=""

#3.读取有关慢日志配置信息
#慢日志存放目录
slowquery_dir="/beta_slowlog/"
#读取当前数据库慢日志路径
slowquery_file=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "show variables like 'slow_query_log_file';" | grep log | awk '{print $2}'`
#设置慢日志时间
slowquery_long_time=2
#pt慢查询工具路径
pt_query_digest="/usr/bin/pt-query-digest"

#4.设置新的慢查询日志路径
slow_log_name=$slowquery_dir`date "+%Y-%m-%d_%H-%M-%S.slow"`
`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password \
-e "set global slow_query_log = 1;set global long_query_time = $slowquery_long_time;set global log_output = 'FILE';set global slow_query_log_file = '$slow_log_name'"`

#5.执行pt命令
$pt_query_digest \
--user=$db_user --password=$db_password --port=$db_port --charset=utf8 \
--review h=$db_host,D=$db_database,t=mysql_slow_query_review  \
--history h=$db_host,D=$db_database,t=mysql_slow_query_review_history  \
--no-report --limit=100% \
--filter=" \$event->{add_column} = length(\$event->{arg})" $slowquery_file > /tmp/slowquery.log
'''


