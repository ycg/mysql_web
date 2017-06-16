#!/bin/bash

host="192.168.1.100"
port=3306
user=root
passwd="123456"

log_dir="/opt/mysql/binlog"
work_dir="/opt/mysql/binlog"
purge_shell="/usr/local/bin/purge_relay_logs"

if [ ! -d ${log_dir} ]
then
   mkdir ${log_dir} -p
fi

${purge_shell}  --host=${host} --user=${user} --password=${passwd} --disable_relay_log_purge --port=${port} --workdir=${work_dir} >> ${log_dir}/purge_relay_logs.log 2>&1


