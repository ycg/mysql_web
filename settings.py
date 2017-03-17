# -*- coding: utf-8 -*-

from monitor import host_info

MySQL_Host = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")
#MySQL_Host = host_info.HoseInfo(host="10.171.251.52", port=3309, user="yangcaogui", password="r_yangcaogui", remark="Monitor")

#一天的秒数
ONE_DAY = 24 * 60 * 60

#监控数据更新间隔
UPDATE_INTERVAL = 2

#Linux主机更新间隔
LINUX_UPDATE_INTERVAL = 5

#Innodb监控更新间隔
INNODB_UPDATE_INTERVAL = 3

#报警间隔
ALARM_INTERVAL = 5

#线程池初始化大小
THREAD_POOL_SIZE = 50

#报表发送时间
REPORT_INTERVAL = 24 * 60 * 60

#检查数据增长量间隔
TABLE_CHECK_INTERVAL = ONE_DAY


EMAIL_HOST = "smtp.exmail.qq.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "sendmail@superjia.com"
EMAIL_HOST_PASSWORD = "Iw2015Many"

