#! /bin/bash

#MySQL慢查询监控脚本
#需要安装pt-tools工具包，然后把脚本设置为后台执行
#注意如果SQL比较长需要修改sample字段为mediumtext
#如果执行set global slow_query_log_file='';报错，注意slow_log目录权限的问题

#alter table table1 modify sample mediumtext not null;
#alter table table1 add column created_time timestamp not null default now(),
#add column updated_time timestamp not null default current_timestamp on update current_timestamp,
#ADD COLUMN `is_reviewed` TINYINT UNSIGNED NOT NULL DEFAULT 0;

#ALTER TABLE `db1`.`mysql_slow_query_review`
#CHANGE COLUMN `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
#DROP PRIMARY KEY,
#ADD PRIMARY KEY (`id`),
#ADD UNIQUE INDEX `checksum_UNIQUE` (`checksum` ASC);

#目前只之前percona分支版本
#set global log_slow_verbosity = 'query_plan,innodb,microtime';

#1.slow log存放的地址
#第一处修改的地方
#慢查询数据上传的MySQL机器
db_host=""
db_port=3306
db_user=""
db_password=""
db_database="mysql_web"

#2.slow log本身的地址
#第二处修改的地方
#监控的慢查询MySQL机器
mysql_client="/usr/local/mysql/bin/mysql"
mysql_host=""
mysql_port=3306
mysql_user=""
mysql_password=""

#3.读取有关慢日志配置信息
#第三处修改的地方，路径不改也没事
slow_log_dir="/slow_log/"
slow_query_long_time=2
pt_query_digest="/usr/bin/pt-query-digest"

#4.mysql_host_id对应着mysql_web.host_infos中id字段值
#第四处修改的地址,这个字段很重要
mysql_host_id=14

function check_slow_log()
{
    #获取slow log文件路径
    slow_log_file=`${mysql_client} -h${mysql_host} -P${mysql_port} -u${mysql_user} -p${mysql_password} \
    -e "show variables like 'slow_query_log_file';" | grep log | awk '{print $2}'`

    echo "$slow_log_file"
    #设置新的slow log文件路径
    slow_log_file_path=${slow_log_dir}${mysql_host_id}_`date "+%Y-%m-%d_%H-%M-%S.slow"`
    `${mysql_client} -h${mysql_host} -P${mysql_port} -u${mysql_user} -p${mysql_password} \
    -e "set global slow_query_log = 1;set global long_query_time=$slow_query_long_time;set global log_output='FILE';set global slow_query_log_file='$slow_log_file_path'"`

    echo "=========================start check================================"
    #对旧的slow log进行解析并入库
    #\$event->{user} !~ m/^serverdev/i 不包含某个用户的过滤，包含就把!改成=
    ${pt_query_digest} \
    --user=${db_user} --password=${db_password} --port=${db_port} --charset=utf8 \
    --review h=${db_host},D=${db_database},t=mysql_slow_query_review  \
    --history h=${db_host},D=${db_database},t=mysql_slow_query_review_history  \
    --no-report --limit=100% --filter=" \$event->{add_column} = length(\$event->{arg}) and \$event->{serverid}=$mysql_host_id and \$event->{user} !~ m/^serverdev/i" ${slow_log_file} > /tmp/slowquery.log

    echo "================check slow log [$slow_log_file] ok===================="
    if [ -f "$slow_log_file" ]; then
        rm -f "$slow_log_file"
        echo "remove $slow_log_file ok."
    fi
    echo ""
}

if [ ! -d "$slow_log_dir" ]; then
    mkdir "$slow_log_dir"
fi

chown -R mysql:mysql ${slow_log_dir}

while true
do
    check_slow_log
    sleep 5m
done
