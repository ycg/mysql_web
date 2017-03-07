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