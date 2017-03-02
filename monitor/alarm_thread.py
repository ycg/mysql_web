# -*- coding: utf-8 -*-

#实现邮件告警，以及数据库健康检查状态的report发送
#告警，包括CPU，内存，线程数，qps和tps等等

import threading, time, cache, mail_util

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
                if(repl_info.io_status == "No" or repl_info.sql_status == "No"):
                    subject = "MySQL - " + repl_info.host_info.remark + "复制异常"
                    text = "IO Status: {0}\nSQL Status: {1}\n".format(repl_info.io_status, repl_info.sql_status)
                    if(len(repl_info.error_message) > 0):
                        text = text + "Error: {1}".format(repl_info.error_message)
                    mail_util.MailUtil().send_text(subject, "yangcaogui.sh@superjia.com", text)