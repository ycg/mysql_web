# -*- coding: utf-8 -*-

import json

from monitor import base_class, cache

#备份
#备份工具mysqldump dumper xtrabackup
#备份方式增量还是全量或者全量+增量
#备份时间每日几点
#备份周期几号全量几号增量
#备份完整性检查|检查备份是否完成是否出现错误

#xtrabackup可以重定向日志，然后去检查日志，可以判断备份是否完成
#备份是否可用，需要进行恢复才行，可以手动

#独特的binlog备份
#binlog备份可以使用mysqlbinlog进行

#指定备份计划

#1.备份名称
#2.选择备份机器
#3.选择备份工具
#4.选择备份方式全量还是增量
#5.选择备份时间-也就是备份周期，根据上面的来，如果是全量那就只有时间，全量+增量会选择周期
#6.填写备份目录-会对这个目录进行检查
#7.备份路径，备份文件
#8.是否需要压缩-只有mysqldump才需要压缩，xtrabackup不需要

#创建备份的时候要对备份进行检查
#路径检查是否合法
#备份存储的机器磁盘是否充足
#是否已经有备份任务
#还有检测是否已经安装过备份工具，三种工具要进行收集，然后统一上传到服务器上
#检查时候已经有了备份计划了
#发送成功和失败邮件

#创建的备份计划也需要建个表
#查看备份任务历史数据-需要建个表

backup_infos = {}

backup_tools = {}
backup_tools[1] = "mydumper"
backup_tools[2] = "mysqldump"
backup_tools[3] = "xtrabackup"

def add_backup(info):
    result_info = check_backup_parameters(info)
    if(result_info.flag == 1):
        info.host_name = cache.Cache().get_host_info(int(info.backup_host_id)).remark
        backup_infos[info.backup_host_id] = info
        result_info.message = "add backup task success."
    return json.loads(result_info)

def check_backup_parameters(info):
    result_info = base_class.BaseClass(None)
    result_info.flag = 1
    if(backup_infos.has_key(info.backup_host_id)):
        result_info.flag = 0
        result_info.message = "此主机的备份任务已经存在"
    elif(len(info.backup_name) <= 0):
        result_info.flag = 0
        result_info.message = "备份名称不能为空"
    elif(len(info.backup_time) <= 0):
        result_info.flag = 0
        result_info.message = "备份时间不能为空"
    return result_info