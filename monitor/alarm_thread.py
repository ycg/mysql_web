# -*- coding: utf-8 -*-

#实现邮件告警，以及数据库健康检查状态的report发送
#告警，包括CPU，内存，线程数，qps和tps等等

import threading, time, cache, mail_util, enum

class AlarmEnum(enum.Enum):
    ReplStatus = 0
    ReplDelay = 1
    CPU = 2
    Memory = 3
    Disk = 4

class AlarmThread(threading.Thread):
    __instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if(AlarmThread.__instance is None):
            AlarmThread.__instance = object.__new__(cls, *args, **kwargs)
        return AlarmThread.__instance

    def load(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while(True):
            time.sleep(2)
            self.alarm_for_replication()

    def alarm_for_replication(self):
        for repl_info in cache.Cache().get_all_repl_infos():
            if(hasattr(repl_info, "io_status") == True):
                error_flag = False
                subject = "MySQL-" + repl_info.host_info.remark
                if(repl_info.io_status == "No" or repl_info.sql_status == "No"):
                    error_flag = True
                    subject = subject + "复制异常"
                elif(repl_info.delay_pos_count > 20000):
                    error_flag = True
                    subject = subject + "复制延迟"
                if(error_flag == True):
                    mail_util.MailUtil().send_text(subject, "yangcaogui.sh@superjia.com", self.get_alarm_for_repl_status_format(repl_info))

    def alarm_for_mysql_status(self):
        pass

    def get_alarm_for_repl_status_format(self, repl_info):
        return "IO Status: {0}\nYes Status: {1}\nDelay Pos: {2}\nError Msg: {3}"\
               .format(repl_info.io_status, repl_info.sql_status, repl_info.delay_pos_count, repl_info.error_message)
