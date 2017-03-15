from monitor import host_info

MySQL_Host = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")
#MySQL_Host = host_info.HoseInfo(host="10.171.251.52", port=3309, user="yangcaogui", password="r_yangcaogui", remark="Monitor")

UPDATE_INTERVAL = 1
LINUX_UPDATE_INTERVAL = 5
INNODB_UPDATE_INTERVAL = 5
ALARM_INTERVAL = 5