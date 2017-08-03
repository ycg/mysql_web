#!/usr/bin/env bash

# 用于在固定时间段收集mysql运行状态信息的脚本
# 参数详解
# host_list 需要收集的mysql机器host列表，已空格分割
# start_timestamp 收集日志的开始时间
# end_timestamp 收集日志的结束时间
# user 数据库用户名
# password 数据库密码
# 注意点：尽量数据库用同一个账号
# 日志保存在/tmp目录下


user=""
password=""
host_list=("192.168.1.101" "192.168.1.102")

start_timestamp=`date +%s -d "2017-08-04 00:49:00"`
stop_timestamp=`date +%s -d "2017-08-04 00:53:00"`
echo ${start_timestamp}, ${stop_timestamp}

innodb_engine_status="show engine innodb status\G"
show_processlist="SELECT * FROM information_schema.processlist where COMMAND != 'Sleep'\G"

function collect_status_log()
{
    for host in ${host_list[*]}
    do
        processlist_file="/tmp/${host}_processlist.txt"
        innodb_status_file="/tmp/${host}_innodb_status.txt"
        echo "-----------------------------------------`date "+%Y-%m-%d %H:%M:%S"`-------------------------------------------" >> ${processlist_file}
        mysql -h${host} -u${user} -p${password} -e"$show_processlist" >> ${processlist_file}
        echo "" >> ${processlist_file}

        echo "-----------------------------------------`date "+%Y-%m-%d %H:%M:%S"`-------------------------------------------" >> ${innodb_status_file}
        mysql -h${host} -u${user} -p${password} -e"$innodb_engine_status" >> ${innodb_status_file}
        echo "" >> ${innodb_status_file}
    done
}

if [ ${start_timestamp} -gt ${stop_timestamp} ]; then
    echo "start time must less then stop time"
    exit
fi

now_timestamp=`date +%s`
while [ ${now_timestamp} -le ${stop_timestamp} ]
do
    if [ ${now_timestamp} -ge ${start_timestamp} ] && [ ${now_timestamp} -le ${stop_timestamp} ]; then
        collect_status_log
        echo "collect ok"
    else
        echo "no collect"
    fi
    sleep 1
    now_timestamp=`date +%s`
done

echo "collect mysql log stop"
