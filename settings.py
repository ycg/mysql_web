# -*- coding: utf-8 -*-

import platform
from monitor.entitys import HoseInfo

MySQL_Host = HoseInfo(host="192.168.11.101", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")

#一天的秒数
ONE_DAY = 24 * 60 * 60

#获取数据库数据的间隔时间
#建议不能小于五秒
UPDATE_INTERVAL = 5

#线程池初始化大小
THREAD_POOL_SIZE = 50

#报表发送时间
REPORT_INTERVAL = 24 * 60 * 60

#检查数据增长量间隔
TABLE_CHECK_INTERVAL = 24 * 60 * 60

EMAIL_HOST = ""
EMAIL_PORT = 25
EMAIL_USER = ""
EMAIL_PASSWORD = ""
EMAIL_SEND_USERS = ""

LINUX_OS = 'Linux' in platform.system()
WINDOWS_OS = 'Windows' in platform.system()


BACKUP_ING = 1
BACKUP_SUCCESS = 2
BACKUP_ERROR = 3

BACKUP_TOOL_MYDUMPER = 1
BACKUP_TOOL_MYSQLDUMP = 2
BACKUP_TOOL_XTRABACKUP = 3

BACKUP_MODE_FULL = 1
BACKUP_MODE_INCREMENT = 2
