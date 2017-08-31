#!/bin/bash

host="192.168.1.100"
port=3306
user=root
password="123456"

#mysql relay log存放的目录
work_dir="/opt/mysql/binlog"
#MHA的purge relay log的脚本路径地址
purge_shell="/usr/local/bin/purge_relay_logs"

#执行MHA的purge脚本
${purge_shell}  --host=${host} --user=${user} --password=${password} --disable_relay_log_purge --port=${port} --workdir=${work_dir} >> /tmp/purge_relay_logs.log 2>&1


#把脚本添加到crontab中去
#* */1 * * * ./purge_relay_log.sh
