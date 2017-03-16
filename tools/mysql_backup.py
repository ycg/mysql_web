# -*- coding: utf-8 -*-

'''
备份脚本：
1.满足mysqldump和xtrabackup的备份选择
2.支持增量和全量备份两种
3.支持备份时间选择
4.支持旧备份数据删除
5.支持配置文件和参数化选择
6.要考虑大数据的备份方案，小数据可以选择mysqldump
7.还可以考虑备份binlog方式
8.备份文件名采用日期+时间的方式
8.mysqldump是否需要压缩

主机id，备份类型=全量，全量加增量

'''

#pip install python-crontab

from crontab import CronTab

host = ""
port = 3306
user = ""
password = ""
backup_path = ""

is_gzip = 0

mysqldump_is_gzip = 0
mysqldump_file_name = ""
mysqldump = "mysqldump -h{0} -u{1} -p{2} -P{3} " \
            "--max-allowed-packet=1G --single-transaction --master-data=2 " \
            "--default-character-set=utf8mb4 --triggers --routines --events -B --all-databases > {4}"


#xtrabackup


#1.检查是全备还是增量备份
#2.增量只支持xtrabackup，通过配置文件


#备份路径
#是否是全量

#如果是增量什么时候增量，什么时候全量
#比如周日全量，其它增量
#

#比如15天备份一个周期，第一天全量，第二天增量
#days=20 说名20备份一个周期

#新建一个文件，专门存储备份目录，放在备份目录下
#backup.txt
#存上一次备份路径用于增量备份 latest_backup_dir=/backup/
#存距离第一次全量备份间隔了多少天 interval_days=1

#定义任务设置，比如晚上几点开始备份
#hour=3 minute=30

#要不要删除备份的数据
#del_days=20 删除20天前的备份

backup_dir = "/backup/"
backup_info = "/backup/backup.txt"
backup_log_dir = "/backup/log/"

interval_days=1
latest_backup_dir = ""

def full_backup():
    pass

def incremental_backup():
    pass

my_cron = CronTab(user=True)

job = my_cron.new(command="echo `date` >> /tmp/time.log")



job.hour.every(5)
job.set_comment("ycg job")
job.setall("*/2 * * * *")

my_cron.write()

print("----------------------------------")
for value in my_cron.crons:
    print(value)

print("ok")