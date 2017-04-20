#!/usr/bin/env bash

host_slave1="db-group2-slave1"
host_slave2="db-group2-slave2"
user="dba_read"
password="abc123!.+"

start_timestamp=`date +%s -d '2017-04-19 04:30:00'`
end_timestamp=`date +%s -d '2017-04-19 05:20:00'`

sql1="show engine innodb status\G"
sql2="SELECT * FROM information_schema.processlist where COMMAND != 'Sleep'\G"

function collect_status()
{
    echo "------------------------`date`-------------------------" >> /tmp/collect.txt

    #show engine innodb status
    echo "--------------------$sql1------------------------------" >> /tmp/collect.txt
    echo "---------------------$host_slave1----------------------" >> /tmp/collect.txt
    mysql -h$host_slave1 -u$user -p$password -e"$sql1" >> /tmp/collect.txt
    echo "---------------------$host_slave2----------------------" >> /tmp/collect.txt
    mysql -h$host_slave2 -u$user -p$password -e"$sql1" >> /tmp/collect.txt

    #show full processlist
    echo "--------------------$sql2------------------------------" >> /tmp/collect.txt
    echo "---------------------$host_slave1----------------------" >> /tmp/collect.txt
    mysql -h$host_slave1 -u$user -p$password -e"$sql2" >> /tmp/collect.txt
    echo "---------------------$host_slave2----------------------" >> /tmp/collect.txt
    mysql -h$host_slave2 -u$user -p$password -e"$sql2" >> /tmp/collect.txt
}

now_timestamp=`date +%s`
while [ $now_timestamp -le $end_timestamp ]
do
    if [ $now_timestamp -ge $start_timestamp ] && [ $now_timestamp -le $end_timestamp ]; then
        collect_status
        echo "collect ok"
    else
        echo "no collect"
    fi
    sleep 1
    now_timestamp=`date +%s`
done
