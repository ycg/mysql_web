# -*- coding: utf-8 -*-

import platform
from monitor.entitys import HoseInfo

MySQL_Host = HoseInfo(host="192.168.11.101", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")

ONE_DAY = 24 * 60 * 60
UPDATE_INTERVAL = 4
THREAD_POOL_SIZE = 50
REPORT_INTERVAL = ONE_DAY
TABLE_CHECK_INTERVAL = ONE_DAY

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

IS_INSERT_MONITOR_LOG = False

MY_KEY = 20

